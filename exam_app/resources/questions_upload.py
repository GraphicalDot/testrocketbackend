# -*- coding: utf-8 -*-
from flask.ext.restful import reqparse, fields, marshal_with

from exam_app import app, db
from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import InvalidUploadSetId, UploadSetAlreadyAdded, UploadSetHasErrors
from exam_app.models.question_upload_set import QuestionUploadSet

from exam_app.auto_upload.upload import add_questions_to_db_and_mock_test


class QuestionUploadSet_(AuthorizedResource):

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
        'parsed_questions_decoded': fields.Raw,
        'parsed_comprehensions_decoded': fields.Raw
    }

    put_response = {
        'error': fields.Boolean(default=False),
        'upload_set': fields.Nested(upload_set_obj)
    }

    get_response = {
        'error': fields.Boolean(default=False),
        'upload_set': fields.Nested(upload_set_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        
        # get the upload set with the given id (with the questions json)
        upload_set = QuestionUploadSet.query.get(kwargs['id'])
        if not upload_set:
            raise InvalidUploadSetId

        # return the upload set
        return {'upload_set': upload_set}

    @marshal_with(put_response)
    def put(self, *args, **kwargs):

        parser = reqparse.RequestParser()
        parser.add_argument('add_questions', type=bool, required=True)
        args = parser.parse_args()

        # check if the upload set exists and `questions_added` is not True
        # and also check if no errors exist in the upload set
        upload_set = QuestionUploadSet.query.get(kwargs['id'])
        if not upload_set:
            raise InvalidUploadSetId
        if upload_set.questions_added is True:
            raise UploadSetAlreadyAdded
        if upload_set.errors_exist is True:
            raise UploadSetHasErrors

        # if all the checks are passed then the upload set can be uploaded
        if args['add_questions']:
            add_questions_to_db_and_mock_test(
                upload_set.parsed_questions_decoded,
                upload_set.parsed_comprehensions_decoded,
                upload_set.mock_test_id
            )

        # set the `questions_added` flag on upload set as True
        upload_set.questions_added = True
        db.session.add(upload_set)
        db.session.commit()

        return {'upload_set': upload_set}


    def delete(self, *args, **kwargs):
        
        # check if the upload set exists and `questions_added` is not True
        upload_set = QuestionUploadSet.query.get(kwargs['id'])
        if not upload_set:
            raise InvalidUploadSetId
        if upload_set.questions_added is True:
            raise UploadSetAlreadyAdded

        # if it is not published then delete it and return a success
        QuestionUploadSet.delete(kwargs['id'])

        return {'success': True, 'error': False}
