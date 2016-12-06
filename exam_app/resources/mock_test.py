# -*- coding: utf-8 -*-

from collections import OrderedDict
import json

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app.models.mock_test import MockTest as MockTestModel
from exam_app.exceptions import InvalidMockTestId, InvalidQuestionId
from exam_app.models import db
from exam_app.resources.mock_test_list import MockTestList
from exam_app.models.question import Question


class MockTest(AuthorizedResource):

    response = {
        'error': fields.Boolean(default=False),
        'mock_test': fields.Nested(MockTestList.mock_test_obj)
    }

    @marshal_with(response)
    def get(self, *args, **kwargs):
        mock_test = MockTestModel.query.get(kwargs['id'])
        if mock_test is None:
            raise InvalidMockTestId
        return {'mock_test': mock_test}

    @marshal_with(response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('is_locked', type=int, choices=[0, 1])
        parser.add_argument('question_ids', type=MockTestList.question_ids_json_type)
        args = parser.parse_args()

        mock_test = MockTestModel.query.get(kwargs['id'])
        if mock_test is None:
            raise InvalidMockTestId

        if args['name'] is not None:
            mock_test.name = args['name']

        if args['question_ids'] is not None:
            args['question_ids'] = json.loads(args['question_ids'])

            for subject_id, data in args['question_ids'].items():
                seen_comprehensions = OrderedDict()
                comp_ques_ids = []
                q_ids = data['q_ids']
                question_data = Question.get_filtertered_list(include_question_ids=q_ids)
                questions = question_data['questions']
                total = question_data['total']

                if total != len(q_ids):
                    raise InvalidQuestionId

                # sort questions in the order in which they appear in `q_ids`
                questions = sorted(questions, key=lambda q: q_ids.index(q.id))

                for question in questions:
                    if question.comprehension_id is not None:
                        # if comprehension not encountered before
                        if question.comprehension_id not in seen_comprehensions:
                            comp_ques_ids.append(question.id)
                            # comprehension questions in order of their ids, i.e order of their addition
                            comprehension_ques_ids = [q.id for q in sorted(question.comprehension.questions.all(), key=lambda q: q.id)]
                            seen_comprehensions[question.comprehension_id] = sorted(comprehension_ques_ids)

                i = 0
                for comp_id, ques_ids in seen_comprehensions.items():
                    ques_id_set = set(ques_ids)
                    ques_id_set.remove(comp_ques_ids[i])
                    # questions ids other than the first encountered question of this comprehension
                    other_comp_ques_ids = ques_id_set
                    # remove qny question ids from `other_comp_ques_ids` if present in `q_ids`
                    for id in other_comp_ques_ids:
                        try:
                            q_ids.remove(id)
                        except:
                            continue
                    # index of first encountered question of this comprehension
                    comp_ques_index = q_ids.index(comp_ques_ids[i])
                    # add all questions of this comprehension to `q_ids` starting from `comp_ques_index`
                    for index, id in enumerate(ques_ids):
                        q_ids.insert(comp_ques_index+index, id)
                    # finally remove the first encountered question of this comprehension from `q_ids`
                    q_ids.remove(q_ids[comp_ques_index+index+1])
                    i += 1

            mock_test.question_ids = json.dumps(args['question_ids'])

        if args['is_locked'] is not None:
            mock_test.is_locked = args['is_locked'] == 1

        db.session.commit()

        return {'mock_test': mock_test}
