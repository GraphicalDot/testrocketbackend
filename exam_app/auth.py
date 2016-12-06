# -*- coding: utf-8 -*-

from exam_app.models import Student, DataOperator, Intern, Teacher, Institute
from exam_app.exceptions import UnknownUserType, AuthenticationFailure
import re


def authenticate_user(user_type, key, secret, by='id'):
    """
    Authenticates a user on the basis of his type. Can be authenticated on the basis of id or email

    :param user_type:
    :param key: email/username
    :param secret:
    :param by: field to be checked for `key`. can be id or email or username. defaults to id
    :return:
    """
    if user_type == 'student':
        user = Student.authenticate_by_email(key, secret) if by == 'email' else Student.authenticate_by_id(key, secret)
    elif user_type == 'data_operator':
        user = DataOperator.authenticate_by_email(key, secret) if by == 'email' else DataOperator.authenticate_by_id(key, secret)
    elif user_type == 'intern':
        user = Intern.authenticate_by_email(key, secret) if by == 'email' else Intern.authenticate_by_id(key, secret)
    elif user_type == 'teacher':
        user = Teacher.authenticate_by_email(key, secret) if by == 'email' else Teacher.authenticate_by_id(key, secret)
    elif user_type == 'institute':
        user = Institute.authenticate_by_username(key, secret) if by == 'username' else Institute.authenticate_by_id(key, secret)
    else:
        raise UnknownUserType

    if user is None:
        raise AuthenticationFailure
    else:
        return user


AUTHORIZATION_MAP = {
    '/questions': {
        'get': ['intern', 'teacher', 'data_operator'],
        'post': ['teacher', 'data_operator'],
    },
    '/questions/$': {
        'get': ['intern', 'teacher', 'data_operator'],
        'put': ['intern', 'teacher', 'data_operator'],
    },

}


id_pattern = re.compile('\/\d+\/|$')


def is_user_authorized(user_type, request_path, request_method):
    """
    Checks if a `user_type` is authorized to perform a particular action(get,post,put) on a particular request path

    :param user_type:
    :param request_path: the path accessed from `request.path`
    :param request_method: the request method(GET,POST,PUT) accessed from `request.method`
    :return: true if authorized, false otherwise
    """
    processed_request_path = re.sub(id_pattern, '/$/', request_path).rstrip('/')
    request_method = request_method.lower()
    return (processed_request_path not in AUTHORIZATION_MAP) or (request_method in AUTHORIZATION_MAP[processed_request_path] and \
        user_type in AUTHORIZATION_MAP[processed_request_path][request_method])
