# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with
from sqlalchemy.exc import IntegrityError

from exam_app.resources.common import AuthorizedResource
from exam_app.models.teacher import Teacher as TeacherModel
from exam_app.exceptions import InvalidTeacherId, EmailAlreadyRegistered
from exam_app.models import db
from exam_app.resources.teacher_list import TeacherList


class Teacher(AuthorizedResource):

    get_response = {
        'error': fields.Boolean(default=False),
        'teacher': fields.Nested({
            'teacher': fields.Nested(TeacherList.teacher_obj),
            'questions_categorized': fields.Integer,
            'questions_approved': fields.Integer,
            'text_solutions_submitted': fields.Integer,
            'text_solutions_approved': fields.Integer,
            'video_solutions_submitted': fields.Integer,
            'video_solutions_approved': fields.Integer,
            'reported_resolved': fields.Integer
        })
    }

    put_response = {
        'error': fields.Boolean(default=False),
        'teacher': fields.Nested(TeacherList.teacher_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        teacher = TeacherModel.get(kwargs['id'])
        return {'teacher': teacher}

    @marshal_with(put_response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str)
        parser.add_argument('subject_expert', type=str, required=True)
        parser.add_argument('specialization', type=str, required=True)
        parser.add_argument('qualification', type=str, required=True)
        args = parser.parse_args()

        teacher = TeacherModel.get(kwargs['id'])

        teacher.name = args['name']
        teacher.email = args['email']
        teacher.subject_expert = args['subject_expert']
        teacher.specialization = args['specialization']
        teacher.qualification = args['qualification']

        if args['password'] is not None:
            teacher.password = md5(args['password']).hexdigest()

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise EmailAlreadyRegistered

        return {'teacher': teacher}
