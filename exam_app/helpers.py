# -*- coding: utf-8 -*-

import uuid
import base64
import csv
import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3CreateError, S3ResponseError
from selenium import webdriver
import sendgrid
from flask import render_template
from itsdangerous import TimestampSigner, SignatureExpired

from exam_app import app
from exam_app.models.past_exam_results import PastExamResult
from exam_app.models.attempted_mock_test import AttemptedMockTest
from exam_app.models import db
from exam_app.exceptions import InvalidAttemptedMockTestId
from exam_app.models.mock_test import MockTest
from exam_app.models.student import Student


#SendGridClient = sendgrid.SendGridClient(app.config['SENDGRID_USER'], app.config['SENDGRID_KEY'])
TIMESTAMP_SIGNER = TimestampSigner(app.config['SECRET_KEY'])


class S3(object):
    def __init__(self, key=None, secret=None):
        if key and secret:
            self.access_key = key
            self.secret = secret
        else:
            self.access_key = app.config['S3_ACCESS_KEY']
            self.secret = app.config['S3_SECRET']
        self.connection = S3Connection(self.access_key, self.secret)
        self.create_bucket = self.connection.create_bucket
        self.get_bucket = self.connection.get_bucket

    @staticmethod
    def _get_content_type(ext):
        if ext == 'jpg':
            return 'image/jpeg'
        if ext == 'png':
            return 'image/png'
        if ext == 'pdf':
            return 'application/pdf'

    def upload(self, data, content_type, make_public=True, bucket=app.config['S3_BUCKET_NAME']):
        bucket_name = bucket
        try:
            bucket = self.get_bucket(bucket_name)
        except S3ResponseError as e:
            if e.error_code == 'NoSuchBucket':
                try:
                    bucket = self.create_bucket(bucket_name)
                except S3CreateError as e:
                    raise e
            else:
                raise e

        s3key = Key(bucket)
        s3key.key = str(uuid.uuid4().get_hex().upper()[0:16]) + '.' + content_type.split('/')[-1]
        s3key.content_type = content_type
        s3key.set_contents_from_string(data)
        if make_public:
            s3key.set_acl('public-read')
        url = 'https://s3.amazonaws.com/' + bucket_name + '/' + s3key.key
        return url


def parse_base64_string(string):
    """
    Parse bas64 data and return the parsed data and mimetype

    :param string:
    :return: mimetype and base64 decoded data
    """
    meta, base64data = string.split(',')
    mimetype = meta.split(';')[0].split(':')[-1]
    return mimetype, base64.decodestring(base64data)


def _parse_string_map(string):
    kvps = string.split(',')
    result = {}
    for kvp in kvps:
        key, value = kvp.split(':')
        # if value is a list
        if ';' in value:
            value = value.split(';')
        result[key] = value

    return result


def insert_exam_data_from_csv(csv_path):
    with open(csv_path, 'rb') as csvfile:
        rows = csv.reader(csvfile, delimiter='|')
        for row in rows:
            year = int(row[0])
            exam = row[1]
            marks_rank = _parse_string_map(row[2])
            rank_college = _parse_string_map(row[3])
            data = {
                'marks_rank': marks_rank,
                'rank_college': rank_college
            }
            print 'entering data for year %d and exam %s' % (year, exam)
            print data
            PastExamResult.insert(year, exam, data)


def create_pdf_report(attempted_mock_test_id):
    host = 'http://localhost'
    if 'HOST' in os.environ:
        host = os.environ['HOST']
    driver = webdriver.PhantomJS('./phantomjs')
    driver.set_window_size(1200, 800)
    file_names = []
    for i in range(1, 6):
        url = host + '/pdf_report/%d?page=page%d' % (attempted_mock_test_id, i)
        driver.get(url)
        file_name = '%d-page%d.pdf' % (attempted_mock_test_id, i)
        file_names.append(file_name)
        driver.save_screenshot(file_name)

    pdf_file_name = 'report_%d.pdf' % attempted_mock_test_id
    cmd = 'convert ' + ' '.join(file_names) + ' ' + pdf_file_name
    # canvas = Canvas(pdf_file_name, pagesize=elevenSeventeen)
    # for i, file_name in enumerate(file_names):
    #     im = Image.open(file_name)
    #     (width, height) = im.size
    #     print width, height
    #     canvas.drawImage(file_name, 0, 0, width=1200, height=800, preserveAspectRatio=True, anchor='nw')
    #     print 'drawn %s' % file_name
    #     if i < (len(file_names) - 1):
    #         canvas.showPage()
    # canvas.save()
    os.system(cmd)
    map(lambda n: os.remove(n), file_names)
    return pdf_file_name


def upload_pdf_report(attempted_mock_test_id):
    with app.app_context():
        amt = AttemptedMockTest.query.get(attempted_mock_test_id)
        if amt is None:
            raise InvalidAttemptedMockTestId
        if amt.pdf_report_url is None:
            pdf_report_file_name = create_pdf_report(amt.id)
            f = open(pdf_report_file_name, 'rb').read()
            s3 = S3()
            pdf_url = s3.upload(f, 'application/pdf')
            os.remove(pdf_report_file_name)
            amt.pdf_report_url = pdf_url
            db.session.commit()
            return pdf_url
        else:
            return amt.pdf_report_url


def _send_email(sender, receiver, subject, html):
    """
    Send email to receiver(s)

    :param sender:
    :param receiver: a string or a list or a tuple or a set
    :param subject:
    :param html:
    :return:
    """
    message = sendgrid.Mail()
    message.set_from(sender)
    # if a list or tuple or set of email passed then to each of them
    if isinstance(receiver, list) or isinstance(receiver, tuple) or isinstance(receiver, set):
        [message.add_to(r) for r in receiver]
    else:
        message.add_to(receiver)
    message.set_subject(subject)
    message.set_html(html)

    SendGridClient.send(message)


def send_email_for_mock_test(attempted_mock_test_id):
    with app.app_context():
        amt = AttemptedMockTest.query.get(attempted_mock_test_id)
        if amt is None:
            raise InvalidAttemptedMockTestId
        mock_test = MockTest.query.get(amt.mock_test_id)
        student = Student.query.get(amt.student_id)
        params = {
            'mock_test_name': mock_test.name,
            'pdf_url': amt.pdf_report_url,
            'mock_test_exam_name': app.config['TARGET_EXAMS'][str(mock_test.target_exam)],
            'student_name': student.name,
            'student_mobile': student.mobile_no,
            'student_email': student.email,
        }

        # html = render_template('mock_test_attempt_complete_email_student.html', **params)
        # _send_email(app.config['TEST_REPORT_EMAIL_SENDER'], student.email,
        #     "Report for test %s" % mock_test.name, html)

        html = render_template('mock_test_attempt_complete_email_teacher.html', **params)
        _send_email(app.config['TEST_REPORT_EMAIL_SENDER'], app.config['PDF_REPORT_EMAIL_RECEIVERS'],
                        "Report for test %s with id %s" % (mock_test.name, str(amt.id)), html)

def send_email_forgot_password(email, reset_url):
    with app.app_context():
        html = render_template('forgot_password_reset_email.html', password_reset_url=reset_url)

    _send_email(app.config['FORGOT_PASSWORD_EMAIL_SENDER'], email, "Password reset link", html)


def get_forgot_password_token(salt):
    string = TIMESTAMP_SIGNER.sign(salt)
    return string


def validate_forgot_password_token(token):
    try:
        TIMESTAMP_SIGNER.unsign(token, max_age=app.config['FORGOT_PASSWORD_LINK_TTL'])
    except SignatureExpired:
        return False
    return True


def send_contact_us_email(data):
    with app.app_context():
        html = render_template('contact_us_form_submit_email.html', **data)

    _send_email(app.config['CONTACT_US_EMAIL_SENDER'], app.config['CONTACT_US_EMAIL_RECEIVERS'], "Someone contacted you for TestRocket", html)


def send_welcome_student_email(data):
    with app.app_context():
        html = render_template('welcome_student_email.html', name=data['name'])

    _send_email(app.config['WELCOME_EMAIL_SENDER'], data['email'], "Welcome to TestRocket", html)


def send_welcome_admin_email(data):
    with app.app_context():
        html = render_template('welcome_admin_email.html', **data)

    _send_email(app.config['WELCOME_EMAIL_SENDER'], data['email'], "Welcome to TestRocket", html)
