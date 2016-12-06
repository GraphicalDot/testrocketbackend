# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app import app
from exam_app.models import db
from exam_app.models.users import UserTypes
from exam_app.models.teacher import Teacher
from exam_app.async_tasks import welcome_admin_email_task


class TeacherList(AuthorizedResource):
    teacher_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'email': fields.String,
        'subject_expert': fields.String,
        'specialization': fields.String,
        'qualification': fields.String,
        'joined_at': fields.DateTime,
        'last_activity': fields.DateTime,
        'type': fields.Integer
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'teachers': fields.List(fields.Nested({
            'teacher': fields.Nested(teacher_obj),
            'questions_categorized': fields.Integer,
            'questions_approved': fields.Integer,
            'text_solutions_submitted': fields.Integer,
            'text_solutions_approved': fields.Integer,
            'video_solutions_submitted': fields.Integer,
            'video_solutions_approved': fields.Integer,
            'reported_resolved': fields.Integer
        })),
        'total': fields.Integer
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'teacher': fields.Nested(teacher_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['TEACHER_LIST_LIMIT'])
        args = parser.parse_args()
        teachers, total = Teacher.get_list(args['page'], args['limit'])
        return {'teachers': teachers, 'total': total}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('subject_expert', type=str, required=True)
        parser.add_argument('specialization', type=str, required=True)
        parser.add_argument('qualification', type=str, required=True)
        args = parser.parse_args()
        teacher = Teacher.create(name=args['name'], email=args['email'], password=md5(args['password']).hexdigest(),
                                subject_expert=args['subject_expert'], specialization=args['specialization'],
                                qualification=args['qualification'])
        data = {
            'name': args['name'],
            'email': args['email'],
            'password': args['password']
        }
        welcome_admin_email_task.delay(data)
        return {'teacher': teacher}
