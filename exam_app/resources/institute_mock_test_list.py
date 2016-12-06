# -*- coding: utf-8 -*-

import json
import itertools

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app import app
from exam_app.models.pushed_mock_test import PushedMockTest
from exam_app.models.mock_test import MockTest
from exam_app.models.batch import Batch


class InstituteMockTestList(AuthorizedResource):
    class JSObject(fields.Raw):
        def format(self, value):
            return json.loads(value)

    mock_test_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'syllabus': fields.String,
        'difficulty': fields.String,
        'target_exam': fields.String,
        'for_institutes': fields.Integer,
        'is_locked': fields.Integer,
        'question_ids': JSObject,
        'type': fields.String,
        'type_id': fields.Integer,
        'prerequisite_id': fields.Integer(default=None),
        'duration': fields.Integer,
        'cutoff': fields.Float,
        'batches_pushed_to': fields.List(fields.Nested({
            'id': fields.Integer,
            'name': fields.String,
            'class': fields.String
        }))
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'mock_tests': fields.List(fields.Nested(mock_test_obj)),
        'total': fields.Integer
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('difficulty', type=str, choices=app.config['MOCK_TEST_DIFFICULTY_LEVEL'].keys())
        parser.add_argument('batches_pushed_to', type=comma_separated_ints_type)
        parser.add_argument('offset', type=int, default=0)
        parser.add_argument('limit', type=int, default=20)
        args = parser.parse_args()
        total = 0
        if args['batches_pushed_to'] is not None:
            pushed_mock_test_ids = {}
            for p in PushedMockTest.query.filter(PushedMockTest.batch_id.in_(args['batches_pushed_to'])).all():
                if p.mock_test_id not in pushed_mock_test_ids:
                    pushed_mock_test_ids[p.mock_test_id] = [p.batch_id]
                else:
                    pushed_mock_test_ids[p.mock_test_id].append(p.batch_id)
            exprs = []
            exprs.append(MockTest.id.in_(pushed_mock_test_ids.keys()))
            if args['difficulty'] is not None:
                exprs.append(MockTest.difficulty == args['difficulty'])
            mock_tests = MockTest.query.filter(*exprs).offset(args['offset']).limit(args['limit'])
            total = MockTest.query.filter(*exprs).count()
            batches = {b.id: b for b in Batch.get_filtered(include_ids=args['batches_pushed_to'])}
        else:
            exprs = []
            exprs.append(MockTest.for_institutes == True)
            exprs.append(MockTest.is_locked == True)
            if args['difficulty'] is not None:
                exprs.append(MockTest.difficulty == args['difficulty'])
            mock_tests = MockTest.query.filter(*exprs).offset(args['offset']).limit(args['limit'])
            batches = {b.id: b for b in Batch.get_filtered(institute_id=kwargs['user'].id)}
            total = MockTest.query.filter(*exprs).count()
            pushed_mock_test_ids = {}
            for p in PushedMockTest.query.filter(PushedMockTest.mock_test_id.in_([m.id for m in mock_tests]),
                                                 PushedMockTest.batch_id.in_(batches.keys())).all():
                if p.mock_test_id not in pushed_mock_test_ids:
                    pushed_mock_test_ids[p.mock_test_id] = [p.batch_id]
                else:
                    pushed_mock_test_ids[p.mock_test_id].append(p.batch_id)
        res = []
        for mock_test in mock_tests:
            mock_test.batches_pushed_to = [{'id': b_id, 'name': batches[b_id].name, 'class': batches[b_id].clazz} for
                                           b_id in pushed_mock_test_ids.get(mock_test.id, [])]
            res.append(mock_test)

        return {'mock_tests': res, 'total': total}