# -*- coding: utf-8 -*-

from flask.views import MethodView
from flask import render_template, redirect, request
from flask.ext.restful import reqparse

from exam_app import app
from exam_app.models import db
from exam_app.models.student import Student
from exam_app.helpers import get_forgot_password_token
from exam_app.async_tasks import send_forgot_password_email


class StudentForgotPassword(MethodView):
    def get(self):
        return render_template('student_forgot_password.html')

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('host', type=str, required=True)
        args = parser.parse_args()
        student = Student.query.filter_by(email=args['email']).first()
        if student is None:
            return render_template('student_forgot_password.html', error='auth', **args)
        else:
            fp_token = get_forgot_password_token(str(student.id))
            student.fp_token = fp_token
            db.session.commit()
            reset_url = args['host'] + '/student_reset_password?token=' + fp_token
            send_forgot_password_email.delay(student.email, reset_url)
            message = 'Check your email for a password reset confirmation link. The link is valid for %s hours only.' % str(app.config['FORGOT_PASSWORD_LINK_TTL']/3600)
            return render_template('student_confirmation_message.html', message=message)