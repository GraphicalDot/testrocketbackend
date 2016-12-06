# -*- coding: utf-8 -*-

from hashlib import md5

from flask.ext.restful import reqparse, fields, marshal_with
from werkzeug.datastructures import FileStorage

from exam_app.resources.common import AuthorizedResource
from exam_app import app
from exam_app.helpers import S3, parse_base64_string
from exam_app.models.institute import Institute
from exam_app.exceptions import UnAcceptableFileType


class InstituteList(AuthorizedResource):
    institute_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'email': fields.String,
        'username': fields.String,
        'location': fields.String,
        'mobile_no': fields.String,
        'logo_url': fields.String,
        'joined_at': fields.DateTime,
        'last_activity': fields.DateTime,
        'type': fields.Integer
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'institutes': fields.List(fields.Nested(institute_obj)),
        'total': fields.Integer
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'institute': fields.Nested(institute_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['INSTITUTE_LIST_LIMIT'])
        args = parser.parse_args()
        institutes, total = Institute.get_list(args['page'], args['limit'])
        return {'institutes': institutes, 'total': total}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('location', type=str, required=True)
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('mobile_no', type=str, required=True)
        parser.add_argument('logo', type=str)
        args = parser.parse_args()

        if args['logo'] is not None:
            s3 = S3()
            mimetype, image_data = parse_base64_string(args['logo'])
            mimetype_parts = mimetype.split('/')
            if len(mimetype_parts) > 1 and mimetype_parts[-1] in app.config['ACCEPTED_IMAGE_EXTENSIONS']:
                # if mimetype has an extension and the extension is in the accepted list then proceed with the upload
                content_type = mimetype_parts[-1]
                url = s3.upload(image_data, content_type)
            else:
                raise UnAcceptableFileType
        else:
            url = None

        institute = Institute.create(name=args['name'], email=args['email'], password=md5(args['password']).hexdigest(),
                                     username=args['username'], location=args['location'], mobile_no=args['mobile_no'],
                                     logo_url=url)

        return {'institute': institute}
