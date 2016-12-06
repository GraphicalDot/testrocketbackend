# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with
from sqlalchemy.exc import IntegrityError

from exam_app.resources.common import AuthorizedResource
from exam_app.models import db
from exam_app.models.data_operator import DataOperator as DataOperatorModel
from exam_app.exceptions import InvalidDataOperatorId, EmailAlreadyRegistered
from exam_app.resources.data_operator_list import DataOperatorList


class DataOperator(AuthorizedResource):

    get_response = {
        'error': fields.Boolean(default=False),
        'data_operator': fields.Nested({
            'data_operator': fields.Nested(DataOperatorList.operator_obj),
            'questions_added': fields.Integer,
            'text_solutions_added': fields.Integer,
            'video_solutions_added': fields.Integer,
        })
    }

    put_response = {
        'error': fields.Boolean(default=False),
        'data_operator': fields.Nested(DataOperatorList.operator_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        data_operator = DataOperatorModel.get(kwargs['id'])
        return {'data_operator': data_operator}

    @marshal_with(put_response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str)
        args = parser.parse_args()

        data_operator = DataOperatorModel.query.get(kwargs['id'])
        if data_operator is None:
            raise InvalidDataOperatorId

        data_operator.name = args['name']
        data_operator.email = args['email']

        if args['password'] is not None:
            data_operator.password = md5(args['password']).hexdigest()

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise EmailAlreadyRegistered

        return {'data_operator': data_operator}
