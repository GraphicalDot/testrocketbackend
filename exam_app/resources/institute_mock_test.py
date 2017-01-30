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

        ##Pushed MockTest tables keeps track of all the mock_tests and all the batches to which they
        ## they have been pushed to. Now the below pushed_batch_ids is the list of the PushedMockTest table
        ## entries where mock_test_id is the id of the mock test in args.
        ## The logic here is that a same test could have been pushed to several batches, but every batch and mock_test
        ## will have seperate entries PushedMockTest, pushed_batch_ids = [batch1, batch5, batch10, ....]
        pushed_batch_ids = [p.batch_id for p in PushedMockTest.query.filter(PushedMockTest.mock_test_id == mock_test.id).all()]
        
        ##NOw Batch model will have several batches in it, we will filter it on the basis of the institute_id and 
        ## the batch_ids

        batches = Batch.get_filtered(include_ids=pushed_batch_ids, institute_id=kwargs['user'].id)
        
        ## Now we aill populate details of all the batches that have this mock_test already attached to it.
        mock_test.batches_pushed_to = [{'id': b.id, 'name': b.name, 'class': b.clazz} for b in batches]
        
        ## Now once the mock_test and its batches been figured out, we will also find all the 
        ## questions associated with it, Every mock_test has a question_ids key corresponding to 
        ## which there is a some bullshit string with two keys order and q_ids like this
        #question_ids    | "{\"1\": {\"order\": 0, \"q_ids\": [31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
        ## 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]}}"

        question_ids = []
        for sid, data in json.loads(mock_test.question_ids).items():
            question_ids.extend(data['q_ids'])
        ##Now based on the q_ids we will have questions from the questions table associated with it.
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