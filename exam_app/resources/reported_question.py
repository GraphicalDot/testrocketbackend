# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse

from exam_app.resources.common import AuthorizedResource
from exam_app.models.reported_question import ReportedQuestion as ReportedQuestionModel


class ReportedQuestion(AuthorizedResource):
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('action', type=str, required=True, choices=['delete', 'resolve'])
        args = parser.parse_args()
        return {'id': 12}

    def delete(self, *args, **kwargs):
        ReportedQuestionModel.delete(kwargs['id'])
        return {'error': False}
