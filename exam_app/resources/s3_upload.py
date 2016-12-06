# -*- coding: utf-8 -*-
from hashlib import sha1
import time, os, json, base64, hmac, urllib, uuid

from exam_app import app

from flask.ext.restful import reqparse, fields, marshal_with
from exam_app.resources.common import AuthorizedResource


class S3RequestSigner(AuthorizedResource):

    def get(self, *args, **kwargs):

        S3_ACCESS_KEY = "AKIAICUCAP6SQJUOJJEQ"
        S3_SECRET = "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"
        S3_BUCKET_NAME = 'testrocket-upload-sets-archives' 
    
        AWS_ACCESS_KEY = S3_ACCESS_KEY
        AWS_SECRET_KEY = S3_SECRET
        S3_BUCKET = S3_BUCKET_NAME

        object_name = urllib.quote_plus(str(uuid.uuid4()) + '.zip')
        mime_type = 'application/zip'

        current_time = time.time()
        expires = int(current_time+60*60*24)
        amz_headers = "x-amz-acl:public-read"

        string_to_sign = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type, expires, amz_headers, S3_BUCKET, object_name)

        signature = base64.encodestring(hmac.new(AWS_SECRET_KEY.encode(), string_to_sign.encode('utf8'), sha1).digest())
        signature = urllib.quote_plus(signature.strip())

        url = 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, object_name)

        response = {
            'signed_request': '%s?AWSAccessKeyId=%s&Expires=%s&Signature=%s' % (url, AWS_ACCESS_KEY, expires, signature),
            'url': url,
            'key_name': object_name,
            'string_to_sign': string_to_sign
        }

        return response
