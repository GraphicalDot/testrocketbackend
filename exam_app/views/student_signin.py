# -*- coding: utf-8 -*-

import json
from hashlib import md5
from base64 import b64encode

from flask.views import MethodView
from flask import render_template, redirect, request
from flask.ext.restful import reqparse

from exam_app import app
from exam_app.auth import authenticate_user
from exam_app.exceptions import AuthenticationFailure


class StudentSignin(MethodView):
    def get(self):
        return render_template('student_signin.html')

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('host', type=str, required=True)
        args = parser.parse_args()
        try:
            student = authenticate_user('student', args['email'], md5(args['password']).hexdigest(), by='email')
        except AuthenticationFailure:
            return render_template('student_signin.html', error='auth', **args)
        token = b64encode(student.email) + '|' + student.password + '|' + str(student.id) + '|' + b64encode(student.name) + '|' + b64encode(','.join(student.target_exams))
        return redirect(args['host'] + app.config['STUDENT_URL']+'#token='+token)