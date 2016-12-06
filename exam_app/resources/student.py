# -*- coding: utf-8 -*-

from exam_app.resources.common import AuthorizedResource
from flask.ext.restful import reqparse, fields, marshal_with


class Student(AuthorizedResource):
    student_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'target_year': fields.Integer,
        'institute': fields.Integer,
        'type': fields.Integer,
        'mobile_no': fields.String,
        'email': fields.String,
        'plan_id': fields.Integer,
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'student': fields.Nested(student_obj)
    }

    @marshal_with(get_response)
    def get(self, id):
        student = {}
        return {'student': student}

    def put(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str)
        parser.add_argument('mobile_no', type=str, required=True)
        parser.add_argument('target_year', type=int, required=True)
        parser.add_argument('institute', type=int, required=True)
        parser.add_argument('plan_id', type=int)
        parser.add_argument('type', type=int, required=True)
        args = parser.parse_args()
        return {'id': 12}
