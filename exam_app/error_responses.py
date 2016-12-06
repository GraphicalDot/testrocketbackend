# -*- coding: utf-8 -*-

"""All the error codes with a human readable message are listed here."""

#from flask.ext.restful import abort


def get_error_response(exception):
    """
    This is used to abort a request in-case of some problem, error etc.

    :param exception: The exception whose error code and message will be used to construct the error response
    :return:
    """
    return api.make_response({'message': exception.message, 'code': exception.error_code, 'error': True}, exception.http_response_code)
    #abort(exception.http_response_code, error=True, message=exception.message, code=exception.error_code)


from exam_app import api
