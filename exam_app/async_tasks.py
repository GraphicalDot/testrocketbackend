# -*- coding: utf-8 -*-
from cStringIO import StringIO
import json

from celery import Celery
from boto.s3.connection import S3Connection

from exam_app.exceptions import ArchiveS3KeyDoesNotExist, InvalidMockTestId, OverallQuestionParsingError, QuestionUploadSetMockSetNotEmpty
from exam_app.models.question_upload_set import QuestionUploadSet
from exam_app.models.mock_test import MockTest
from exam_app.auto_upload.upload import check_if_errors_exist_in_parsed_questions
from exam_app.auto_upload.parse import parse_paper
from exam_app import app
from exam_app.helpers import upload_pdf_report, send_email_for_mock_test, send_email_forgot_password, \
    send_contact_us_email, send_welcome_student_email, send_welcome_admin_email


celery_app = Celery('app', broker=app.config['BROKER_URL'])
celery_app.conf.update(
    CELERYD_FORCE_EXECV=True
)

class ExceptionJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Exception):
            return obj.message
        else:
            return super(ExceptionJSONEncoder, self).default(obj)

@celery_app.task
def upload_report_and_send_email(attempted_mock_test_id):
    upload_pdf_report(attempted_mock_test_id)
    send_email_for_mock_test(attempted_mock_test_id)


@celery_app.task
def send_forgot_password_email(email, reset_url):
    send_email_forgot_password(email, reset_url)


@celery_app.task
def contact_us_email_task(data):
    send_contact_us_email(data)


@celery_app.task
def welcome_student_email_task(data):
    send_welcome_student_email(data)


@celery_app.task
def welcome_admin_email_task(data):
    send_welcome_admin_email(data)

@celery_app.task
def parse_upload_set_async(name, s3_key, mock_test_id):

        ctx = app.test_request_context()
        ctx.push()

        print 'yeah baby!'

        # check if the s3 key exists
        conn = S3Connection(app.config['S3_ACCESS_KEY'], app.config['S3_SECRET'])
        bucket = conn.get_bucket(app.config['S3_UPLOAD_SET_ARCHIVES_BUCKET'])
        archive_s3 = bucket.get_key(s3_key)
        print 'S3 Key: {0}'.format(s3_key)
        if not archive_s3:
            raise ArchiveS3KeyDoesNotExist

        # check if the mock test is open and has no questions
        mock_test = MockTest.query.get(mock_test_id)
        if not mock_test:
            raise InvalidMockTestId
        if not mock_test.question_ids is None:
            raise QuestionUploadSetMockSetNotEmpty

        # parse the paper and store it in json
        archive = StringIO()
        archive_s3.get_contents_to_file(archive)

        parsed_questions = parse_paper(archive)

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
            name=name,
            errors_exist=errors,
            mock_test_id=mock_test.id,
            parsed_questions=ExceptionJSONEncoder().encode(parsed_questions['questions']),
            parsed_comprehensions=ExceptionJSONEncoder().encode(parsed_questions['comprehensions'])
        )

        print 'yeah baby done!!!'

        ctx.pop()

        return True
