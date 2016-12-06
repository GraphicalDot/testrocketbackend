# -*- coding: utf-8 -*-

import datetime, json

import requests

from exam_app import app


class Log(object):

    @staticmethod
    def _send_log_to_loggly(tag, log_level, exception, traceback, context=None):

        log_json = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'ExcName': exception.__class__.__name__,
            'Msg': unicode(exception.message),
            'TraceBack': traceback,
            'LogLevel': log_level,
            'TrackingID': 'DEV',
            'Categorytag': tag
        }
        if context: log_json['Context'] = context

        loggly_url = app.config['LOGGLY_URL'] + '/{tag}/'.format(tag=tag)
        requests.post(loggly_url, json.dumps(log_json))

    @staticmethod
    def error(tag, exception, traceback, context=None):
        """Log error level messages."""

        Log._send_log_to_loggly(
            tag = tag,
            log_level = 'ERROR',
            exception = exception,
            traceback = traceback,
            context = context
        )

    @staticmethod
    def warn(tag, exception, traceback, context=None):
        """Log warning level messages."""

        Log._send_log_to_loggly(
            tag = tag,
            log_level = 'WARN',
            exception = exception,
            traceback = traceback,
            context = context
        )

    @staticmethod
    def debug(tag, exception, traceback, context=None):
        """Log debug level messages."""

        Log._send_log_to_loggly(
            tag = tag,
            log_level = 'DEBUG',
            exception = exception,
            traceback = traceback,
            context = context
        )

    @staticmethod
    def verbose(tag, exception, traceback, context=None):
        """Log verbose level messages."""

        Log._send_log_to_loggly(
            tag = tag,
            log_level = 'VERBOSE',
            exception = exception,
            traceback = traceback,
            context = context
        )
