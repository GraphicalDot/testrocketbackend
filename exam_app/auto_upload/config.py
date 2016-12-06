# -*- coding: utf-8 -*-

QUESTION_ATTRIBUTES_NAMES = ['Nature', 'Difficulty', 'Type', 'Time']

BS_EXTRA_SPACES_NOT_NEEDED = ['\n', '\r']

QUESTION_NATURE = {
    '1': 'Formula Based',
    '2': 'Theoritical',
    '3': 'Concept Based / Conceptual',
    '4': 'Application Based',
    '5': 'Multi application based'
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
QUESTION_DIFFICULTY_LEVEL = map(str, range(1, 6))

QUESTION_ATTRIBUTES_SIMILARITY_THRESHOLD = 90

QUESTION_STATUS = {
    # keeping string values of 0 and 1 because postgres hstore needs keys and values as text
    'categorized': '0',
    'proof_read_categorization': '0',
    'text_solution_added': '0',
    'video_solution_added': '0',
    'proof_read_text_solution': '0',
    'proof_read_video_solution': '0',
    'finalized': '0',
    'error_reported': '0'
}


BS_EXTRA_TAGS = ['o:p']

S3_BUCKET_NAME = 'testrocket-papers-temp'
S3_ACCESS_KEY = "AKIAICUCAP6SQJUOJJEQ"
S3_SECRET = "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"
