# -*- coding: utf-8 -*-

import os
try:
    from value_id_map import SUBJECT_ID_MAP
except ImportError:
    # When file not present use values these values
    SUBJECT_ID_MAP = {
        'Physics': 58,
        'Chemistry': 59,
        'Mathematics': 60,
        'Biology': 44,
        'English Proficency': 53,
        'Logical Reasoning': 54,
        'GK': 55,
        'Scholastic Aptitude Test': 1738,
        'Language Comprehensive Test': 1845,
        'Mental Ability Test': 1866
    }


class Config(object):

    DEBUG = True # setting debug as true by default for some heroku testing

    SECRET_KEY = 'a-secret'
    QUESTION_BANK_LIST_LIMIT = 10
    REPORTED_QUESTION_LIST_LIMIT = 10
    TEACHER_LIST_LIMIT = 10
    DATA_OPERATOR_LIST_LIMIT = 10
    INTERN_LIST_LIMIT = 10
    STUDENT_LIST_LIMIT = 10
    INSTITUTE_LIST_LIMIT = 10
    MOCK_TEST_LIST_LIMIT = 10
    DEFAULT_AVERAGE_TIME = 60   # 60 seconds
    UPLOAD_SET_LIST_LIMIT = 20

    S3_ACCESS_KEY = "AKIAICUCAP6SQJUOJJEQ"
    S3_SECRET = "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"
    S3_BUCKET_NAME = 'testrocket-question-files-final'
    S3_UPLOAD_SET_ARCHIVES_BUCKET = 'testrocket-upload-sets-archives'
    S3_QUESTION_FILES_TEMP_BUCKET = 'testrocket-question-files-temp'
    S3_QUESTION_FILES_FINAL_BUCKET = 'testrocket-question-files-final'

    AUTO_UPLOAD_DTP_ID = 1
    AUTO_UPLOAD_TEACHER_ID = 3


    ACCEPTED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg']

    LOGGLY_URL = 'https://logs-01.loggly.com/inputs/7714e078-e66a-4d04-a124-ea4bb3dde77d/tag/python/'

    SENDGRID_USER = 'lovesh_h'
    SENDGRID_KEY = 'lovesh123'
    TEST_REPORT_EMAIL_SENDER = 'TestRocket <hello@testrocket.in>'
    FORGOT_PASSWORD_EMAIL_SENDER = 'TestRocket <hello@testrocket.in>'
    FORGOT_PASSWORD_LINK_TTL = 48 * 60 * 60
    CONTACT_US_EMAIL_RECEIVERS = ['rishabh95verma@gmail.com', 'divyashish.jindal@gmail.com']
    CONTACT_US_EMAIL_SENDER = 'TestRocket <hello@testrocket.in>'
    WELCOME_EMAIL_SENDER = 'TestRocket <hello@testrocket.in>'
    PDF_REPORT_EMAIL_RECEIVERS = ['me@rishabhverma.me',]

    """
    marking scheme is in the format
        <exam1>: {
            <subject_id1>: {
                <question_type1>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type2>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
            },
            <subject_id2>: {
                <question_type1>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type3>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
            },
            <subject_id3>: {
                <question_type1>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type2>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type3>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type4>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
            },

        },
        <exam2>: {
            <subject_id1>: {
                <question_type2>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type3>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
            },
            <subject_id3>: {
                <question_type5>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type1>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
            },
            <subject_id5>: {
                <question_type1>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type5>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type6>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
                <question_type6>: {
                    correct: <+ve marks>,
                    incorrect: <marks which can be -ve or 0>,
                    not_attempted: <marks which can be +ve or -ve or 0>
                },
            },
        },
    """
    MARKING_SCHEME = {
        '1': {                                  # exam 1, mean JEE Advanced here
            SUBJECT_ID_MAP['Physics']: {                              # subject id 1, means physics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {                          # question type 2, means Multiple Correct here
                    'correct': 3,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '3': {                          # question type 3, means Single/Multi Correct here, added by lovesh, might need to change
                    'correct': 4,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '4': {                          # question type 4, means Comprehension here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {                          # question type 5, means Matrix match here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {                          # question type 6, means Integer here
                    'correct': 3,
                    'incorrect': 0,
                    'not_attempted': 0
                }
            },
            SUBJECT_ID_MAP['Chemistry']: {                              # subject id 2, means chemistry here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {                          # question type 2, means Multiple Correct here
                    'correct': 3,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '3': {                          # question type 3, means Single/Multi Correct here, added by lovesh, might need to change
                    'correct': 4,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '4': {                          # question type 4, means Comprehension here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {                          # question type 5, means Matrix match here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {                          # question type 6, means Integer here
                    'correct': 3,
                    'incorrect': 0,
                    'not_attempted': 0
                }
            },
            SUBJECT_ID_MAP['Mathematics']: {                              # subject id 2, means mathematics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {                          # question type 2, means Multiple Correct here
                    'correct': 3,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '3': {                          # question type 3, means Single/Multi Correct here, added by lovesh, might need to change
                    'correct': 4,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '4': {                          # question type 4, means Comprehension here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {                          # question type 5, means Matrix match here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {                          # question type 6, means Integer here
                    'correct': 3,
                    'incorrect': 0,
                    'not_attempted': 0
                }
            },
        },
        '2': {                                  # exam 2 means JEE Mains here
            SUBJECT_ID_MAP['Physics']: {                              # subject id 1, means physics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {                          # question type 2, means Multiple Correct here, added by lovesh, might need to change
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {                          # question type 3, means Single/Multi Correct here, added by lovesh, might need to change
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['Chemistry']: {                              # subject id 143, means chemistry here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {                          # question type 2, means Multiple Correct here, added by lovesh, might need to change
                    'correct': 4,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '3': {                          # question type 3, means Single/Multi Correct here, added by lovesh, might need to change
                    'correct': 5,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['Mathematics']: {                              # subject id 2, means mathematics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {                          # question type 2, means Multiple Correct here, added by lovesh, might need to change
                    'correct': 4,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '3': {                          # question type 3, means Single/Multi Correct here, added by lovesh, might need to change
                    'correct': 5,
                    'incorrect': 0,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            }
        },
        '3': {                                  # exam 3 means BITSAT here
            SUBJECT_ID_MAP['Physics']: {                              # subject id 1, means physics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['Chemistry']: {                              # subject id 2, means chemistry here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['Mathematics']: {                              # subject id 3, means mathematics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['English Proficency']: {                              # subject id 3, means english here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                }
            },
            SUBJECT_ID_MAP['Logical Reasoning']: {                              # subject id 38, means Logical Reasoning here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            }
        },
        '4': {                                  # exam 4 means AIPMT here
            SUBJECT_ID_MAP['Physics']: {                              # subject id 1, means physics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['Chemistry']: {                              # subject id 2, means chemistry here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                }
            },
            SUBJECT_ID_MAP['Biology']: {                              # subject id 16, means bio here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 4,
                    'incorrect': -1,
                    'not_attempted': 0
                },
            },
        },
        '5': {                                  # exam 5 means AIIMS here
            SUBJECT_ID_MAP['Physics']: {                              # subject id 1, means physics here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['Chemistry']: {                              # subject id 2, means chemistry here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['Biology']: {                              # subject id 16, means bio here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -0.33,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
            },
            SUBJECT_ID_MAP['GK']: {                              # subject id 39, means General Knowledge here
                '1': {                          # question type 1, means Single Correct here
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '2': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '3': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '4': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '5': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
                '6': {
                    'correct': 3,
                    'incorrect': -.33,
                    'not_attempted': 0
                },
            },
        },

        # '6': { # for NTSE
        #     SUBJECT_ID_MAP['Scholastic Aptitude Test']: {
        #         '1': { # Single Correct Question
        #             'correct': 1,
        #             'incorrect': 0,
        #             'not_attempted': 0
        #         },
        #         '4': { # Comprehension type of question
        #             'correct': 1,
        #             'incorrect': 0,
        #             'not_attempted': 0
        #         },
        #     },
        #     SUBJECT_ID_MAP['Language Comprehensive Test']: {                              # subject id 2, means chemistry here
        #         '1': { # Single Correct Question
        #             'correct': 1,
        #             'incorrect': 0,
        #             'not_attempted': 0
        #         },
        #         '4': { # Comprehension type of question
        #             'correct': 1,
        #             'incorrect': 0,
        #             'not_attempted': 0
        #         },
        #     },
        #     SUBJECT_ID_MAP['Mental Ability Test']: {                              # subject id 2, means chemistry here
        #         '1': { # Single Correct Question
        #             'correct': 1,
        #             'incorrect': 0,
        #             'not_attempted': 0
        #         },
        #         '4': { # Comprehension type of question
        #             'correct': 1,
        #             'incorrect': 0,
        #             'not_attempted': 0
        #         },
        #     },
        # },


    }

    QUESTION_OVER_TIME = 10

    PAYMENT_PLAN = {
        '1': 500,         # free full test
        '2': 500,         # free part test
        '3': 500,         # free subject test
        '4': 500          # free chapter test
    }

    TARGET_EXAM_WEIGHT = {
        '1': 1,
        '2': 1,
        '3': 1,
        '4': 1,
        '5': 1,
    }

    TOP_PERFORMERS_PERCENTAGE = 50
    BOTTOM_PERFORMERS_PERCENTAGE = 50
    TOP_PERFORMERS_MIN_COUNT = 5
    BOTTOM_PERFORMERS_MIN_COUNT = 5
    TOP_TOPICS_COUNT = 5
    BOTTOM_TOPICS_COUNT = 5

    # Dont change the following once db is created. If you do, then alter tables and enums accordingly.

    # Used for setting max length of columns.
    EMAIL_MAX_LENGTH = 200
    USERNAME_MAX_LENGTH = 100
    PASSWORD_MAX_LENGTH = 64
    NAME_MAX_LENGTH = 200
    MOBILE_NO_MAX_LENGTH = 13
    URL_MAX_LENGTH = 500
    TEST_NAME_MAX_LENGTH = 100
    QUESTION_UPLOAD_SET_NAME_MAX_LENGTH = 100

    # Used for various enums
    ONTOLOGY_NODE_TYPES = {'1': 'Chapter', '2': 'Broad Category', '3': 'Topic', '4': 'Sub Topic', '5': 'Sub-Sub Topic'}

    ONTOLOGY_NODE_CLASSES = {'1': 'Class 11', '2': 'Class 12', '3': 'NTSE'}

    TARGET_EXAMS = {'1': 'JEE Advanced', '2': 'JEE Mains', '3': 'BITSAT', '4': 'AIPMT', '5': 'AIIMS', '6': 'NTSE'}

    MOCK_TEST_DIFFICULTY_LEVEL = {'1': 'Easy', '2': 'Medium', '3': 'Hard'}

    MOCK_TEST_TYPES = {'1': 'Full Test', '2': 'Part Test', '3': 'Subject Test', '4': 'Chapter Test'}

    QUESTION_DIFFICULTY_LEVEL = map(str, range(1, 6))

    QUESTION_NATURE = {
        '1': 'Formula Based',
        '2': 'Theory Based',
        '3': 'Concept Based',
        '4': 'Application Based',
        '5': 'Multiapplication based'
    }

    QUESTION_TYPE = {
        '1': 'Single Correct',
        '2': 'MultiCorrect',
        '3': 'Single/Multi Correct',
        '4': 'Comprehension',
        '5': 'Matrix Match',
        '6': 'Integer'
    }

    QUESTION_AVERAGE_TIME = map(str, range(30, 330, 30))

    BATCH_FIELD = {'1': 'Engineering', '2': 'Medical'}

    BATCH_TYPE = {'1': 'Class 11', '2': 'Class 12', '3': 'Droppers', '4': 'Other'}

    STUDENT_BRANCHES = {'1': 'Engineering', '2': 'Medical', '3': 'Commerce', '4': 'Civil Services'}

    SUBMISSION_STATUS = ['accepted', 'rejected']


class ProductionConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    STUDENT_URL = '/app.html'
    INSTITUTE_URL = '/app.html'
    BROKER_URL = os.environ.get('REDISTOGO_URL')


class DevelopmentConfig(Config):
    DEBUG = True
    _POSTGRES = {
        'host': 'localhost',
        'user': 'postgres2',
        'password': 'postgres',
        'database': 'exam_prep'
    }
    STUDENT_URL = '/student/app.html'
    INSTITUTE_URL = '/institute/app.html'
    # SQLALCHEMY_DATABASE_URI = "postgres://uf54hnqr1b2g67:p6c2vrn9q7oqtd947n6frgrcguh@ec2-54-243-188-17.compute-1.amazonaws.com:5922/dcnft6j1pljtlb"
    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(password)s@%(host)s/%(database)s' % _POSTGRES
    BROKER_URL = 'redis://localhost:6379/10'
