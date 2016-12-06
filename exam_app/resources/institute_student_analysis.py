# -*- coding: utf-8 -*-

import json
from copy import deepcopy

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app import app
from exam_app.resources.attempted_mock_test_list import AttemptedMockTestList
from exam_app.resources.attempted_mock_test import AttemptedMockTest
from exam_app.resources.mock_test_list import MockTestList
from exam_app.resources.question_list import QuestionList


class InstituteStudentAnalysis(AuthorizedResource):

    class JSObject(fields.Raw):
        def format(self, value):
            return json.loads(value)

    attempted_mock_test_obj = {
        'id': fields.Integer,
        'pushed_mock_test_id': fields.Integer,
        'mock_test_id': fields.Integer,
        'score': fields.Float,
        'answers': JSObject,
        'analysis': JSObject,
        'attempted_at': fields.String
    }

    attempted_mock_test = deepcopy(AttemptedMockTestList.attempted_mock_test_obj)
    attempted_mock_test['pdf_report_url'] = fields.String

    response = {
        'error': fields.Boolean(default=False),
        'attempted_mock_tests': fields.List(fields.Nested(attempted_mock_test_obj)),
        'mock_tests': fields.List(fields.Nested(MockTestList.mock_test_obj)),
        'questions': fields.List(fields.Nested(QuestionList.question_obj)),
        'accuracy': fields.Float,
        'speed': fields.Float,
        'attempted_mock_test': fields.Nested(attempted_mock_test),
        'mock_test': fields.Nested(MockTestList.mock_test_obj),
    }

    @marshal_with(response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('student_id', type=int, required=True)
        parser.add_argument('attempted_mock_test_id', type=int)
        args = parser.parse_args()
        # if no attempted mock test id provided return cumulative analysis
        if args['attempted_mock_test_id'] is None:
            return AttemptedMockTestList.get_cumulative_analysis(args['student_id'], kwargs['user'].id)
        else:
            return AttemptedMockTest.get_analysis(args['attempted_mock_test_id'])