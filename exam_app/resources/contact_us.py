# -*- coding: utf-8 -*-

from flask import request
from flask.ext.restful import reqparse, Resource

from exam_app.async_tasks import contact_us_email_task


class ContactUsSubmitEmail(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('message', type=str, required=True)
        args = parser.parse_args()
        contact_us_email_task.delay(args)
        return {
            'error': False
        }
