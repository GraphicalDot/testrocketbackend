# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource, comma_separated_ints_type
from exam_app import app
from exam_app.resources.question_list import QuestionList
from exam_app.models import ReportedQuestion


class ReportedQuestionList(AuthorizedResource):
    report_obj = {
        'question': fields.Nested(QuestionList.question_obj),
        'report_id': fields.Integer
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'reports': fields.List(fields.Nested(report_obj)),
        'total': fields.Integer
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('categorized', type=int, default=1)

        # the next field will contain comma separated ontology node ids
        parser.add_argument('ontology', type=comma_separated_ints_type)

        parser.add_argument('nature', type=str, choices=app.config['QUESTION_NATURE'].keys())
        parser.add_argument('type', type=str, choices=app.config['QUESTION_TYPE'].keys())
        parser.add_argument('difficulty', type=str, choices=app.config['QUESTION_DIFFICULTY_LEVEL'])
        parser.add_argument('average_time', type=str, choices=map(int, app.config['QUESTION_AVERAGE_TIME']))
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['REPORTED_QUESTION_LIST_LIMIT'])
        args = parser.parse_args()
        reports, total = ReportedQuestion.get(args['nature'], args['type'], args['difficulty'],
                                                    args['average_time'], args['ontology'], args['page'], args['limit'])
        return {'reports': reports, 'total': total}

    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('question_id', type=int, required=True)
        args = parser.parse_args()
        report = ReportedQuestion.create(kwargs['user_type'].id, kwargs['user'].id, args['question_id'])
        return {'report_id': report.id}
