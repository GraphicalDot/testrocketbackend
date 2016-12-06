# -*- coding: utf-8 -*-

import json
from copy import deepcopy

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import InvalidStudentId, InvalidMockTestId, InvalidAttemptedMockTestId, InvalidQuestionId
from exam_app import app
from exam_app.models.student import Student
from exam_app.models.mock_test import MockTest
from exam_app.models.question import Question
from exam_app.models.attempted_mock_test import AttemptedMockTest as AttemptedMockTestModel
from exam_app.models.past_exam_results import PastExamResult
from exam_app.models.ontology import Ontology
from exam_app.resources.attempted_mock_test_list import AttemptedMockTestList
from exam_app.resources.mock_test_list import MockTestList
from exam_app.resources.question_list import QuestionList
from exam_app.models import db


class AttemptedMockTest(AuthorizedResource):

    class JSObject(fields.Raw):
        def format(self, value):
            return json.loads(value)

    attempted_mock_test = deepcopy(AttemptedMockTestList.attempted_mock_test_obj)
    attempted_mock_test['pdf_report_url'] = fields.String

    get_response = {
        'error': fields.Boolean(default=False),
        'attempted_mock_test': fields.Nested(attempted_mock_test),
        'mock_test': fields.Nested(MockTestList.mock_test_obj),
        'questions': fields.List(fields.Nested(QuestionList.question_obj)),
    }

    @classmethod
    def get_percentile(cls, attempted_mock_test):
        # attempted mock test with same `mock_test_id`
        similar_tests = AttemptedMockTestModel.query.filter(AttemptedMockTestModel.mock_test_id == attempted_mock_test.mock_test_id).all()
        if len(similar_tests) > 0:
            similar_test_scores = [test.score for test in similar_tests]
            sorted_scores = sorted(similar_test_scores)
            scores_more, scores_less = filter(lambda s: s > attempted_mock_test.score, sorted_scores), filter(lambda s: s < attempted_mock_test.score, sorted_scores)
            if len(scores_more) == 0 and len(scores_less) == 0:
                return 0.0
            else:
                return len(scores_less)*100.0/len(sorted_scores)

    @classmethod
    def get_rank_and_college(cls, attempted_mock_test, mock_test):
        past_exams = PastExamResult.query.filter_by(exam=mock_test.target_exam).order_by(PastExamResult.year.desc())
        if past_exams is not None:
            last_exam = past_exams.first()
            if last_exam is not None:
                last_exam_data = json.loads(last_exam.data)
                #attempted_mock_test.analysis['last_year_cutoff'] = last_exam_data['cutoff']
                marks_ranks = [[map(int, marks_range.split('~')), map(int, rank_range.split('~'))] for marks_range, rank_range in last_exam_data['marks_rank'].items()]
                obtained_marks_range = None
                closest_obtained_marks_range = None
                for item in marks_ranks:
                    marks_low = item[0][0]
                    marks_high = item[0][1]
                    if marks_low <= attempted_mock_test.score <= marks_high:
                        obtained_marks_range = [[marks_low, marks_high], item[1]]
                        break
                    else:
                        if closest_obtained_marks_range is None:
                            closest_obtained_marks_range = [[marks_low, marks_high], item[1]]
                        else:
                            if abs(attempted_mock_test.score - closest_obtained_marks_range[0][0]) > abs(attempted_mock_test.score - marks_low):
                                closest_obtained_marks_range = [[marks_low, marks_high], item[1]]
                if obtained_marks_range is None:
                    obtained_marks_range = closest_obtained_marks_range
                obtained_marks_range[1].reverse()
                expected_rank = '%s-%s' % (obtained_marks_range[1][0], obtained_marks_range[1][1])

                ranks_colleges = [[map(int, rank_range.split('~')), colleges] for rank_range, colleges in last_exam_data['rank_college'].items()]
                ranks_colleges = sorted(ranks_colleges, key=lambda x: int(x[0][0]))
                obtained_rank_range = None
                closest_obtained_rank_range = None
                for item in ranks_colleges:
                    rank_low = item[0][0]
                    rank_high = item[0][1]
                    if rank_low <= obtained_marks_range[1][0] and obtained_marks_range[1][1] <= rank_high:
                        obtained_rank_range = [[rank_low, rank_high], item[1]]
                        break
                    else:
                        if obtained_marks_range[1][0] <= rank_high:
                            if closest_obtained_rank_range is None:
                                closest_obtained_rank_range = [[rank_low, rank_high], item[1]]
                            else:
                                if rank_low <= obtained_marks_range[1][0] and obtained_marks_range[1][1] > rank_high:
                                    if (obtained_marks_range[1][0] - rank_low) > (obtained_marks_range[1][0] - closest_obtained_rank_range[0][0]):
                                        closest_obtained_rank_range = [[rank_low, rank_high], item[1]]
                                if rank_low > obtained_marks_range[1][0] and obtained_marks_range[1][1] <= rank_high:
                                    if (rank_high - obtained_marks_range[1][1]) > (obtained_marks_range[1][1] - closest_obtained_rank_range[0][1]):
                                        closest_obtained_rank_range = [[rank_low, rank_high], item[1]]

                if obtained_rank_range is None and closest_obtained_rank_range is not None:
                    obtained_rank_range = closest_obtained_rank_range
                if obtained_rank_range is None and closest_obtained_rank_range is None:
                    obtained_rank_range = [[], ['No colleges expected']]
                expected_colleges = obtained_rank_range[1]
                return expected_rank, expected_colleges

    @staticmethod
    def get_analysis(attempted_mock_test_id):
        attempted_mock_test = AttemptedMockTestModel.query.get(attempted_mock_test_id)
        if attempted_mock_test is None:
            raise InvalidAttemptedMockTestId
        mock_test = MockTest.query.get(attempted_mock_test.mock_test_id)
        if mock_test is None:
            raise InvalidMockTestId

        if attempted_mock_test.answers is None:
            return {'error': True, 'message': 'No answers yet'}

        attempted_mock_test.analysis = json.loads(attempted_mock_test.analysis)

        attempted_mock_test.analysis['percentile'] = AttemptedMockTest.get_percentile(attempted_mock_test)

        attempted_mock_test.analysis['cutoff'] = mock_test.cutoff
        rank_colleges = AttemptedMockTest.get_rank_and_college(attempted_mock_test, mock_test)
        if rank_colleges is not None:
            attempted_mock_test.analysis['expected_rank'], attempted_mock_test.analysis['expected_colleges'] = rank_colleges

        attempted_mock_test.analysis = json.dumps(attempted_mock_test.analysis)

        question_data = json.loads(mock_test.question_ids)
        question_ids = []
        for subject_id, data in question_data.items():
            data['subject_id'] = subject_id
            question_ids.extend(data['q_ids'])
        questions = Question.get_filtertered_list(include_question_ids=question_ids)['questions']

        return {'attempted_mock_test': attempted_mock_test, 'mock_test': mock_test, 'questions': questions}

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        attempted_mock_test_id = kwargs['id']
        return self.get_analysis(attempted_mock_test_id)