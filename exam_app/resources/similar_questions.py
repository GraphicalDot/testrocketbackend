# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse, fields, marshal_with
from sqlalchemy import or_

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app.models.question import Question
from exam_app.models import db
from exam_app import app
from exam_app.resources.common import comma_separated_ints_type
from exam_app.resources.question_list import QuestionList


class SimilarQuestions(AuthorizedResource):

    get_response = {
        'error': fields.Boolean(default=False),
        'questions': fields.List(fields.Nested(QuestionList.question_obj)),
        'total': fields.Integer
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        """
        Get questions questions not similar to the given question id

        :param args:
        :param kwargs:
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument('nature', type=str, choices=app.config['QUESTION_NATURE'].keys())
        parser.add_argument('type', type=str, choices=app.config['QUESTION_TYPE'].keys())
        parser.add_argument('difficulty', type=str, choices=app.config['QUESTION_DIFFICULTY_LEVEL'])
        parser.add_argument('average_time', type=int, choices=map(int, app.config['QUESTION_AVERAGE_TIME']))

        # this contains comma separated ontology node ids
        parser.add_argument('ontology', type=comma_separated_ints_type)

        parser.add_argument('question_id', type=int)

        parser.add_argument('offset', type=int, default=0)

        args = parser.parse_args()

        if args['question_id'] is None:
            exprs = [Question.is_similarity_marked == False, Question.status['categorized'] == '1']
            if args['nature'] is not None:
                exprs.append(Question.nature == args['nature'])
            if args['type'] is not None:
                exprs.append(Question.type == args['type'])
            if args['difficulty'] is not None:
                exprs.append(Question.difficulty == args['difficulty'])
            if args['average_time'] is not None:
                exprs.append(Question.average_time == args['average_time'])
            if args['ontology'] is not None:
                exprs.append(Question.ontology == args['ontology'])

            question = Question.query.filter(*exprs).offset(args['offset']).first()
            if question is None:
                return {'questions': [], 'total': 0}
            else:
                other_questions = Question.get_filtertered_list(nature=args['nature'], type=args['type'], difficulty=args['difficulty'],
                                         average_time=args['average_time'], ontology=args['ontology'], categorized='1', exclude_question_ids=[question.id,])

                if other_questions['total'] == 0:
                    skip = args['offset'] + 1
                    while question is not None:
                        question = Question.query.filter(*exprs).offset(skip).first()
                        if question is None:
                            return {'questions': [], 'total': 0}
                        other_questions = Question.get_filtertered_list(nature=args['nature'], type=args['type'], difficulty=args['difficulty'],
                                         average_time=args['average_time'], ontology=args['ontology'], categorized='1', exclude_question_ids=[question.id,])
                        if other_questions['total'] > 0:
                            break
                        skip += 1

                return {
                    'questions': [question] + other_questions['questions'],
                    'total': other_questions['total']+1
                }
        else:
            question_id = args['question_id']
            question = Question.get(question_id)

            other_questions = Question.get_filtertered_list(ontology=question.ontology, categorized='1', exclude_question_ids=[question.id,])

            return {
                'questions': [question] + other_questions['questions'],
                'total': other_questions['total'] + 1
            }

    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('question_id', type=int, required=True)

        # this contains comma separated question ids
        parser.add_argument('similar_question_ids', type=str)

        args = parser.parse_args()

        lst = map(lambda x: x.strip(), args['similar_question_ids'].split(','))
        if '' in lst:
            similar_question_ids = []
        else:
            similar_question_ids = map(int, lst)

        question = Question.query.get(args['question_id'])
        question.is_similarity_marked = True
        question.similar_question_ids = similar_question_ids
        similar_questions = Question.query.filter(Question.id.in_(similar_question_ids), or_(Question.similar_question_ids == None, Question.similar_question_ids.any(question.id))).all()
        for q in similar_questions:
            if q.similar_question_ids is None:
                q.similar_question_ids = [question.id]
            else:
                q.similar_question_ids.append(question.id)
        db.session.commit()
        return {'error': False}
