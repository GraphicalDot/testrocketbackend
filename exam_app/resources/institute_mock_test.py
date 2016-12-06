# -*- coding: utf-8 -*-

import datetime
import json

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app.exceptions import InvalidMockTestId
from exam_app.models import db
from exam_app.models.pushed_mock_test import PushedMockTest
from exam_app.models.mock_test import MockTest
from exam_app.models.batch import Batch
from exam_app.resources.institute_mock_test_list import InstituteMockTestList
from exam_app.resources.question_list import QuestionList
from exam_app.models.question import Question


class InstituteMockTest(AuthorizedResource):
    response = {
        'error': fields.Boolean(default=False),
        'mock_test': fields.Nested(InstituteMockTestList.mock_test_obj),
        'questions': fields.List(fields.Nested(QuestionList.question_obj))
    }

    @marshal_with(response)
    def get(self, *args, **kwargs):
        mock_test = MockTest.query.get(kwargs['id'])
        if mock_test is None:
            raise InvalidMockTestId
        pushed_batch_ids = [p.batch_id for p in PushedMockTest.query.filter(PushedMockTest.mock_test_id == mock_test.id).all()]
        batches = Batch.get_filtered(include_ids=pushed_batch_ids, institute_id=kwargs['user'].id)
        mock_test.batches_pushed_to = [{'id': b.id, 'name': b.name, 'class': b.clazz} for b in batches]
        question_ids = []
        for sid, data in json.loads(mock_test.question_ids).items():
            question_ids.extend(data['q_ids'])
        questions = Question.get_filtertered_list(include_question_ids=question_ids)['questions']
        return {'mock_test': mock_test, 'questions': questions}

    @marshal_with(response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('batch_ids', type=comma_separated_ints_type, required=True)
        args = parser.parse_args()
        mock_test = MockTest.query.get(kwargs['id'])
        if mock_test is None:
            raise InvalidMockTestId
        batches = {b.id: b for b in Batch.get_filtered(institute_id=kwargs['user'].id)}
        new_batch_ids = args['batch_ids'][:]
        for p in PushedMockTest.query.filter(PushedMockTest.mock_test_id == mock_test.id, PushedMockTest.batch_id.in_(batches.keys())).all():
            if p.batch_id in args['batch_ids']:
                new_batch_ids.remove(p.batch_id)

        for batch_id in new_batch_ids:
            p = PushedMockTest(mock_test_id=mock_test.id, batch_id=batch_id, pushed_at=datetime.datetime.utcnow())
            db.session.add(p)
        db.session.commit()
        return {'error': False}