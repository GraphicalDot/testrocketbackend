# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app import app
from exam_app.resources.common import comma_separated_ints_type
from exam_app.models.student import Student


class StudentList(AuthorizedResource):
    student_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'email': fields.String,
        'target_year': fields.Integer,
        'institute': fields.Integer,
        'type': fields.Integer,
        'mobile_no': fields.String,
        'city': fields.String,
        'branches': fields.List(fields.String),
        'target_exams': fields.List(fields.String),
        'father_name': fields.String,
        'father_mobile_no': fields.String,
        'payment_plan_id': fields.String,
        'registered_from': fields.String
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'students': fields.List(fields.Nested(student_obj)),
        'total': fields.Integer
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'student': fields.Nested(student_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('type', type=int, default=0)
        parser.add_argument('institute', type=int, default=0)
        parser.add_argument('target_year', type=int, default=0)
        parser.add_argument('status', type=int, default=0)
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['STUDENT_LIST_LIMIT'])
        args = parser.parse_args()
        students, total = Student.get_list(args['page'], args['limit'])
        return {'students': students, 'total': total}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('mobile_no', type=str, required=True)
        parser.add_argument('target_year', type=int, required=True)
        parser.add_argument('city', type=str)
        parser.add_argument('area', type=str)
        parser.add_argument('branches', type=comma_separated_ints_type, required=True)
        parser.add_argument('target_exams', type=comma_separated_ints_type, required=True)
        parser.add_argument('father_name', type=str)
        parser.add_argument('father_mobile_no', type=str)
        args = parser.parse_args()

        student = Student.create(name=args['name'], email=args['email'], password=md5(args['password']).hexdigest(), mobile_no=args['mobile_no'],
                                 target_year=args['target_year'], city=args['city'], area=args['area'], branches=args['branches'],
                                 target_exams=args['target_exams'], father_name=args['father_name'],
                                 father_mobile_no=args['father_mobile_no'])
        return {'student': student}
