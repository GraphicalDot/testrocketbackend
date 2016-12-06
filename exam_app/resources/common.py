# -*- coding: utf-8 -*-

from functools import wraps

from flask.ext.restful import Resource
from flask import request

from exam_app.error_responses import get_error_response
from exam_app.exceptions import AuthenticationFailure, UnknownUserType, UnauthorizedToAccess
from exam_app.auth import authenticate_user, is_user_authorized
from exam_app.models.users import UserTypes


def auth_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        """
        Authenticates and authorizes the user

        :param args:
        :param kwargs:
        :return:
        """

        # check if  basic auth params present in the request
        auth = request.authorization
        if not auth:
            raise AuthenticationFailure

        # check if basic auth `username` matches the pattern `<user_type>|<user_id>`
        try:
            user_type, user_id = auth.username.split('|')
        except ValueError:
            raise AuthenticationFailure

        # Check user_id and password pair
        try:
            user = authenticate_user(user_type, user_id, auth.password)
        except (UnknownUserType, AuthenticationFailure) as e:
            raise e

        # Check if user is authorized to access the requested path
        if is_user_authorized(user_type, request.path, request.method):
            kwargs['user_type'] = UserTypes.query.get(user.type)
            kwargs['user'] = user
            user.update_last_active_to_now()
            return f(*args, **kwargs)
        else:
            raise UnauthorizedToAccess

    return decorated


class AuthorizedResource(Resource):
    method_decorators = [auth_user]


def comma_separated_ints_type(arg):
    """
    Used in request parsers for parsing string of format "2,3, 5, 10,2", Returns a list of integers or raises ValueError

    :param arg: string
    :return: list
    """
    if isinstance(arg, basestring):
        lst = map(lambda x: x.strip(), arg.split(','))
        try:
            return map(int, lst)
        except:
            pass

    raise ValueError("Cannot parse string into list of integers")
