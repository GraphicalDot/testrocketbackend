# -*- coding: utf-8 -*-

from collections import Counter
import json

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import InvalidStudentId, InvalidMockTestId
from exam_app.models.question import Question
from exam_app.models.mock_test import MockTest
from exam_app.resources.mock_test_list import MockTestList
from exam_app.resources.question_list import QuestionList
from pprint import pprint 

class StudentMockTestQuestions(AuthorizedResource):
    get_response = {
        'error': fields.Boolean(default=False),
        'mock_test': fields.Nested(MockTestList.mock_test_obj),
        'subjects': fields.List(fields.Nested({
            'questions': fields.List(fields.Nested(QuestionList.question_obj)),
            'subject_id': fields.Integer,
            'order': fields.Integer,
            'q_ids': fields.List(fields.Integer)
        }))
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('mock_test_id', type=int, required=True)
        args = parser.parse_args()
        mock_test_id = args['mock_test_id']
        mock_test = MockTest.query.get(mock_test_id)
        if mock_test is None:
            raise InvalidMockTestId
        question_data = json.loads(mock_test.question_ids)
        question_ids = []
        for subject_id, data in question_data.items():
            data['subject_id'] = subject_id
            question_ids.extend(data['q_ids'])

        sorted_question_data = sorted(question_data.values(), key=lambda d: d['order'])
        questions = Question.get_filtertered_list(include_question_ids=question_ids)['questions']


        """
        for question in questions:
            print '--options--'
            print question.correct_options
            print '---$$$---'
            question.correct_options = None
            question.option_reasons = None
            question.text_solution = None
            question.video_solution_url = None
            question.similar_question_ids = None
            question.average_time = None
        """

        questions = {q.id: q for q in questions}
        for subject in sorted_question_data:
            subject['questions'] = map(lambda q_id: questions[q_id], subject['q_ids'])
        
        pprint({'mock_test': mock_test, 'subjects': sorted_question_data})
        return {'mock_test': mock_test, 'subjects': sorted_question_data}
