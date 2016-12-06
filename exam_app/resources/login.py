# -*- coding: utf-8 -*-

from hashlib import md5

from flask import request
from flask.ext.restful import reqparse, Resource

from exam_app.auth import authenticate_user


class Login(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('key', type=str, required=True)
        parser.add_argument('secret', type=str, required=True)
        parser.add_argument('user_type', type=str, required=True, choices=['student', 'data_operator', 'intern', 'teacher', 'institute'])
        args = parser.parse_args()
        user = authenticate_user(args['user_type'], args['key'], md5(args['secret']).hexdigest(), by='email')
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
