# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with
from werkzeug.datastructures import FileStorage
from sqlalchemy.exc import IntegrityError
from flask import request

from exam_app.resources.common import AuthorizedResource
from exam_app.models.institute import Institute as InstituteModel
from exam_app.resources.institue_list import InstituteList
from exam_app.helpers import S3, parse_base64_string
from exam_app.models import db
from exam_app.exceptions import EmailAlreadyRegistered, UnAcceptableFileType, UsernameAlreadyRegistered, MobileNoAlreadyRegistered
from exam_app import app


class Institute(AuthorizedResource):

    response = {
        'error': fields.Boolean(default=False),
        'institute': fields.Nested(InstituteList.institute_obj)
    }

    @marshal_with(response)
    def get(self, *args, **kwargs):
        institute = InstituteModel.get(kwargs['id'])
        return {'institute': institute}

    @marshal_with(response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str)
        parser.add_argument('location', type=str, required=True)
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('mobile_no', type=str, required=True)
        parser.add_argument('logo', type=str)
        args = parser.parse_args()

        institute = InstituteModel.get(kwargs['id'])
        institute.name = args['name']
        institute.email = args['email']
        institute.location = args['location']
        institute.username = args['username']
        institute.mobile_no = args['mobile_no']

        if args['password'] is not None:
            institute.password = md5(args['password']).hexdigest()

        if args['logo'] is not None:
            s3 = S3()
            mimetype, image_data = parse_base64_string(args['logo'])
            mimetype_parts = mimetype.split('/')
            if len(mimetype_parts) > 1 and mimetype_parts[-1] in app.config['ACCEPTED_IMAGE_EXTENSIONS']:
                # if mimetype has an extension and the extension is in the accepted list then proceed with the upload
                content_type = mimetype_parts[-1]
                url = s3.upload(image_data, content_type)
                institute.logo_url = url
            else:
                raise UnAcceptableFileType

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            if 'email' in e.message:
                raise EmailAlreadyRegistered
            if 'username' in e.message:
                raise UsernameAlreadyRegistered
            if 'mobile_no' in e.message:
                raise MobileNoAlreadyRegistered
            raise e

        return {'institute': institute}
