# -*- coding: utf-8 -*-
import uuid, json
from cStringIO import StringIO

from flask.ext.restful import reqparse, fields, marshal_with
from werkzeug import FileStorage
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from exam_app import app
from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import ArchiveS3KeyDoesNotExist, InvalidMockTestId, OverallQuestionParsingError, QuestionUploadSetMockSetNotEmpty
from exam_app.models.mock_test import MockTest
from exam_app.models.question_upload_set import QuestionUploadSet
from exam_app.auto_upload.parse import parse_paper
from exam_app.auto_upload.upload import check_if_errors_exist_in_parsed_questions
from exam_app.helpers import parse_base64_string

from exam_app.async_tasks import parse_upload_set_async

class ExceptionJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Exception):
            return obj.message
        else:
            return super(ExceptionJSONEncoder, self).default(obj)

class QuestionsFileUpload(AuthorizedResource):

    post_response = {
        'error': fields.Boolean(default=False),
        'archive_s3_key': fields.String
    }
    
    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=str, required=True)
        args = parse.parse_args()

        # create a file object of the image
        mimetype, file_data = parse_base64_string(args['file'])
        archive_file = StringIO(file_data)

        print 'yahan pahuncha 1'

        # upload the file to s3 with a unique uuid
        key_name = str(uuid.uuid4()) + '.zip'
        conn = S3Connection(app.config['S3_ACCESS_KEY'], app.config['S3_SECRET'])
        bucket = conn.get_bucket(app.config['S3_UPLOAD_SET_ARCHIVES_BUCKET'])
        archive_s3 = Key(bucket)
        archive_s3.key = key_name
        archive_s3.content_type = 'application/zip'
        archive_s3.set_contents_from_string(archive_file.getvalue())
        archive_s3.set_acl('public-read')

        print 'yahan pahuncha 2'

        # close the StringIO object
        archive_file.close()

        print 'yahan pahuncha 3'
        
        # return the name of the S3 key
        return {'archive_s3_key': archive_s3.key}

class QuestionUploadSetList(AuthorizedResource):

    mock_test_obj = {
        'name': fields.String
    }

    upload_set_obj = {
        'id': fields.Integer,
        'name': fields.String,
        'errors_exist': fields.Boolean,
        'mock_test_id': fields.Integer,
        'mock_test': fields.Nested(mock_test_obj),
        'questions_added': fields.Boolean,
    }

    get_response = {
        'total': fields.Integer,
        'error': fields.Boolean(default=False),
        'upload_sets': fields.List(fields.Nested(upload_set_obj)),
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'upload_set': fields.Nested(upload_set_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=app.config['UPLOAD_SET_LIST_LIMIT'])
        args = parser.parse_args()

        # get a list of all the upload sets in the DB (without the questions)
        upload_set_pag_obj = QuestionUploadSet.query.filter().order_by(QuestionUploadSet.created_at.desc()).paginate(args['page'], args['limit'])
        upload_sets = upload_set_pag_obj.items
        total = upload_set_pag_obj.total

        # return a list of tests
        return {'upload_sets': upload_sets, 'total': total}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        
        parse = reqparse.RequestParser()
        parse.add_argument('name', type=str, required=True)
        parse.add_argument('archive_key', type=str, required=True)
        parse.add_argument('mock_test_id', type=str, required=True)
        args = parse.parse_args()

        parse_upload_set_async.delay(args['name'], args['archive_key'], args['mock_test_id'])

        print 'this is done'

        return 'this is good shit'

        #print 'Checking S3 key'

        # check if the s3 key exists
        conn = S3Connection(app.config['S3_ACCESS_KEY'], app.config['S3_SECRET'])
        bucket = conn.get_bucket(app.config['S3_UPLOAD_SET_ARCHIVES_BUCKET'])
        archive_s3 = bucket.get_key(args['archive_key'])
        if not archive_s3:
            raise ArchiveS3KeyDoesNotExist

        #print 'S3 key checked'


        #print 'Checking mock test'

        # check if the mock test is open and has no questions
        mock_test_id = args['mock_test_id']
        mock_test = MockTest.query.get(mock_test_id)
        if not mock_test:
            raise InvalidMockTestId
        if not mock_test.question_ids is None:
            raise QuestionUploadSetMockSetNotEmpty

        #print 'Mock test checked'

        #print 'Getting contents from S3'

        # parse the paper and store it in json
        archive = StringIO()
        archive_s3.get_contents_to_file(archive)

        #print 'Contents from S3 got'
        
        #print 'parsing questions'
        parsed_questions = parse_paper(archive)
        #print 'questions parsed'

        # check the parsed questions for any `overall` errors. if there are then don't proceed
        if parsed_questions['is_overall_error']:
            error_message = '\n'.join([ exc.message for exc in parsed_questions['overall_errors'] ])
            raise OverallQuestionParsingError(error_message)

        # check if any errors exist or not
        errors = False
        try:
            check_if_errors_exist_in_parsed_questions(parsed_questions)
        except Exception as e:
            errors = True

        # store the parsed questions in the DB
        upload_set = QuestionUploadSet.create(
            name=args['name'],
            errors_exist=errors,
            mock_test_id=mock_test.id,
            parsed_questions=ExceptionJSONEncoder().encode(parsed_questions['questions']),
            parsed_comprehensions=ExceptionJSONEncoder().encode(parsed_questions['comprehensions'])
        )

        return {'upload_set': upload_set}
