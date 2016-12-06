# -*- coding: utf-8 -*-

from hashlib import md5

from flask.views import MethodView
from flask import render_template, redirect, request
from flask.ext.restful import reqparse

from exam_app import app
from exam_app.models import db
from exam_app.models.institute import Institute
from exam_app.helpers import validate_forgot_password_token


class InstituteResetPassword(MethodView):
    def get(self):
        return render_template('institute_reset_password.html')

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('host', type=str, required=True)
        parser.add_argument('token', type=str, required=True)
        args = parser.parse_args()
        institute = Institute.query.filter_by(fp_token=args['token']).first()
        if institute is None:
            message = 'The link from where you came here is not a proper link'
            return render_template('institute_confirmation_message.html', message=message)
        else:
            if validate_forgot_password_token(args['token']):
                institute.password = md5(args['password']).hexdigest()
                institute.fp_token = None
                db.session.commit()
                return render_template('institute_signin.html', reset=True)
            else:
                message = 'Password reset link expired.'
                return render_template('institute_confirmation_message.html', message=message)