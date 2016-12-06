# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app import app
from exam_app.models.data_operator import DataOperator
from exam_app.models.users import UserTypes
from exam_app.async_tasks import welcome_admin_email_task


class DataOperatorList(AuthorizedResource):
    operator_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'email': fields.String,
        'joined_at': fields.DateTime,
        'last_activity': fields.DateTime,
        'type': fields.Integer
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'data_operators': fields.List(fields.Nested({
            'data_operator': fields.Nested(operator_obj),
            'questions_added': fields.Integer,
            'text_solutions_added': fields.Integer,
            'video_solutions_added': fields.Integer
        })),
        'total': fields.Integer
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'data_operator': fields.Nested(operator_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['DATA_OPERATOR_LIST_LIMIT'])
        args = parser.parse_args()

        rows, total = DataOperator.get_list(args['page'], args['limit'])
        return {'data_operators': rows, 'total': total}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        data_operator = DataOperator.create(name=args['name'], email=args['email'], password=md5(args['password']).hexdigest())
        welcome_admin_email_task.delay(args)
        return {'data_operator': data_operator}
