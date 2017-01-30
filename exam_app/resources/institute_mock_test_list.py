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
    ##{difficulty: 0, batches_pushed_to: 0, page: 1, limit: 10, offset: 0}
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('difficulty', type=str, choices=app.config['MOCK_TEST_DIFFICULTY_LEVEL'].keys())
        parser.add_argument('batches_pushed_to', type=comma_separated_ints_type)
        parser.add_argument('offset', type=int, default=0)
        parser.add_argument('limit', type=int, default=20)
        args = parser.parse_args()
        total = 0
        print args
        if args['batches_pushed_to'] is not None:
            pushed_mock_test_ids = {}
            #gets all the n etries from the PushedMockTest Model where batchid matches the batches_pushed_to in the args
            #batches_pushed_to probably is from institutte mock_test.js when a user clicks on mock_tests_list.js
            ## As it is obvious there could be multiple entries in PushedMockTest for a particular batch
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
            print "From line 75 institute_mock_test_list.py" + batches
        else:
            exprs = []
            exprs.append(MockTest.for_institutes == True)
            exprs.append(MockTest.is_locked == True)
            if args['difficulty'] is not None:
                exprs.append(MockTest.difficulty == args['difficulty'])

            ##Filtering mocktests based on the factors if mock is for institutes , whther it is locked
            ## whats the difficulty of the mock_test and the offsetting on offset and limit
            mock_tests = MockTest.query.filter(*exprs).offset(args['offset']).limit(args['limit'])

            ##Now filtering batches on the basis of the insitutes id
            batches = {b.id: b for b in Batch.get_filtered(institute_id=kwargs['user'].id)}
            total = MockTest.query.filter(*exprs).count()
            
            ##batches list will have all the batches based on the filters and have institue ids meant for this 
            ##institute
            ## Till now mock_tests is the list of all the mocks tests which are meant for this 
            ## institute, and are locked and have difficulty level provided in the args(when user filtes on the difficulty
            ## on the institue panel under /mock_tests) on institue panel
            ## Filter PushedMockTest.mock_test_id.in_([m.id for m in mock_tests])
            ##         this will filter PushedMockTest entries for which mock_test id is matching for mock test
            ##         based on the filters, i.e PushedMockTest entries where mocktests are meant for institues and are locked
            ##
            ## Filter: PushedMockTest.batch_id.in_(batches.keys()))
            ##         All the PushedMockTest entries where the batches are created by this institute
            ## If we combine these filters then the result from PushedMockTest
            ## will be the entries which have batch_id made by this institute and mock tests which are meant for 
            ## this institute
            ## for example lets say this istitute has an id 2
            ##
            ## And lets say pushed_mock_test has following entries
            ## id           | 1
            # mock_test_id | 4
            # batch_id     | 1
            # pushed_at    | 2017-01-28 20:49:29.714396
            # expires_at   | 
            # -[ RECORD 2 ]+---------------------------
            # id           | 2
            # mock_test_id | 5
            # batch_id     | 1
            # pushed_at    | 2017-01-28 21:05:51.978209
            # expires_at   | 


            pushed_mock_test_ids = {}
            for p in PushedMockTest.query.filter(PushedMockTest.mock_test_id.in_([m.id for m in mock_tests]),
                                                 PushedMockTest.batch_id.in_(batches.keys())).all():
                if p.mock_test_id not in pushed_mock_test_ids:
                    pushed_mock_test_ids[p.mock_test_id] = [p.batch_id]
                else:
                    pushed_mock_test_ids[p.mock_test_id].append(p.batch_id)
            print pushed_mock_test_ids
            ##{4: [1], 5: [1]}
            ##this pushed_mock_test_ids will create a dict with each mock test that has been pushed for this 
            ## institute as a key and a value which is all the batches to which this mock test has been assigned

            ## clazz in an array [11, 12]

        res = []
        for mock_test in mock_tests:
            mock_test.batches_pushed_to = [{'id': b_id, 'name': batches[b_id].name, 'class': batches[b_id].clazz} for
                                           b_id in pushed_mock_test_ids.get(mock_test.id, [])]
            res.append(mock_test)
            ##pushed_mock_test_ids.get(mock_test.id, []) because a same mock test would have been pushed to multiple 
            ## batches, in that case pushed_mock_test_ids would have a list of batches corresponding
            ## to a mock test
        return {'mock_tests': res, 'total': total}