# -*- coding: utf-8 -*-

import os,sys
import traceback

from flask import Flask, request
from flask.ext.restful import Api

from exam_app.exceptions import TestAppException


app = Flask(__name__)

if 'mode' in os.environ and os.environ['mode'] == 'production':
    app.config.from_object('exam_app.config.ProductionConfig')
else:
    app.config.from_object('exam_app.config.DevelopmentConfig')


from exam_app.models import db


def init_sqlalchemy(app):
    print "Running sqlalchemy init function"
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app

app = init_sqlalchemy(app)


from exam_app.logger import Log


class MyApi(Api):
    def handle_error(self, e):
        if isinstance(e, TestAppException):
            return get_error_response(e)

        code = getattr(e, 'code', 500)
        if 499 < code < 600:
            tag = request.method + ' ' + request.path
            exc = traceback.format_exc()
            context = 'local'
            if 'environment' in os.environ:
                if os.environ['environment'] == 'production':
                    context = 'production'
                if os.environ['environment'] == 'staging':
                    context = 'staging'
            Log.error(tag, e, exc, context)
            print exc
            sys.stdout.flush()
            return self.make_response({'message': 'something went wrong', 'trace': exc}, 500)
        return super(MyApi, self).handle_error(e)

api = MyApi(app)


# CORS headers
@app.after_request
def add_access_control_headers(response):
    """Adds the required access control headers"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization,Content-Type,X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'POST,GET,PUT,DELETE'
    response.headers['Cache-Control'] = 'No-Cache'
    return response


from exam_app.resources import *


api.add_resource(Login, '/login')
api.add_resource(DataOperator, '/data_operator/<int:id>')
api.add_resource(DataOperatorList, '/data_operator')
api.add_resource(Institute, '/institute/<int:id>')
api.add_resource(InstituteList, '/institute')
api.add_resource(Intern, '/intern/<int:id>')
api.add_resource(InternList, '/intern')
api.add_resource(Ontology, '/ontology/<int:id>')
api.add_resource(OntologyTree, '/ontology')
api.add_resource(Question, '/question/<int:id>')
api.add_resource(QuestionList, '/question')
api.add_resource(ReportedQuestion, '/reported_question/<int:id>')
api.add_resource(ReportedQuestionList, '/reported_question')
api.add_resource(Teacher, '/teacher/<int:id>')
api.add_resource(TeacherList, '/teacher')
api.add_resource(CategorySubmission, '/category_submission/<int:id>')
api.add_resource(CategorySubmissionList, '/category_submission')
api.add_resource(SolutionSubmission, '/solution_submission/<int:id>')
api.add_resource(SolutionSubmissionList, '/solution_submission')
api.add_resource(Student, '/student/<int:id>')
api.add_resource(StudentList, '/student')
api.add_resource(MockTest, '/mock_test/<int:id>')
api.add_resource(MockTestList, '/mock_test')
api.add_resource(SimilarQuestions, '/similar_questions')
api.add_resource(StudentMockTestList, '/student_mock_test')
api.add_resource(StudentMockTestQuestions, '/student_mock_test_questions')
api.add_resource(AttemptedMockTestList, '/attempted_mock_test')
api.add_resource(AttemptedMockTest, '/attempted_mock_test/<int:id>')
api.add_resource(Batch, '/batch/<int:id>')
api.add_resource(BatchList, '/batch')
api.add_resource(InstituteStudent, '/institute_student/<int:id>')
api.add_resource(InstituteStudentList, '/institute_student')
api.add_resource(InstituteMockTest, '/institute_mock_test/<int:id>')
api.add_resource(InstituteMockTestList, '/institute_mock_test')
api.add_resource(ContactUsSubmitEmail, '/contact_us')
api.add_resource(InstituteAnalysis, '/institute_analysis')
api.add_resource(InstituteStudentAnalysis, '/institute_student_analysis')

api.add_resource(QuestionsFileUpload, '/question_upload_set/upload_file')
api.add_resource(QuestionUploadSetList, '/question_upload_set')
api.add_resource(QuestionUploadSet_, '/question_upload_set/<int:id>')

api.add_resource(S3RequestSigner, '/sign_s3_question_upload')


from exam_app.views import *


# app.add_url_rule('/123_456_789_123_student_signup', view_func=StudentSignup.as_view('student_signup'))
app.add_url_rule('/student_signup', view_func=StudentSignup.as_view('student_signup'))
app.add_url_rule('/student_signin', view_func=StudentSignin.as_view('student_signin'))
app.add_url_rule('/pdf_report/<int:id>', view_func=PdfReport.as_view('pdf_report'))
app.add_url_rule('/institute_signin', view_func=InstituteSignin.as_view('institute_signin'))
app.add_url_rule('/student_forgot_password', view_func=StudentForgotPassword.as_view('student_forgot_password'))
app.add_url_rule('/student_reset_password', view_func=StudentResetPassword.as_view('student_reset_password'))
app.add_url_rule('/institute_forgot_password', view_func=InstituteForgotPassword.as_view('institute_forgot_password'))
app.add_url_rule('/institute_reset_password', view_func=InstituteResetPassword.as_view('institute_reset_password'))


from exam_app.error_responses import get_error_response
