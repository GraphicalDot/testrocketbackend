# -*- coding: utf-8 -*-
import json, os

from bs4 import BeautifulSoup
from boto.s3.connection import S3Connection

from exam_app import db, app
from exam_app.models.mock_test import MockTest
from exam_app.models.ontology import Ontology
from exam_app.models.question import Question
from exam_app.models.comprehension import Comprehension
from exam_app.models.solution_submission import SolutionSubmission
from exam_app.models.category_submission import CategorySubmission
from exam_app.auto_upload import config
from exam_app.auto_upload.parse import parse_paper
from exam_app.auto_upload.exceptions import QuestionPaperParsingError


def check_if_errors_exist_in_parsed_questions(paper_questions):
    """Iterates through the list of questions returned by `parse_paper`
    and checks if there are any errors in the same. Raises an exception
    if an error exists.
    """

    ## Raise exceptions if there are any errors in the parsed paper
    if paper_questions['is_overall_error'] is True:
        raise QuestionPaperParsingError(u'Some errors existed in the paper.')
    for question in paper_questions['questions']:
        # check attribute errors
        if question['attributes']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question attributes.')
        if question['attributes']['nature']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question attributes.')
        if question['attributes']['difficulty']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question attributes.')
        if question['attributes']['type']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question attributes.')
        if question['attributes']['average_time']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question attributes.')
        # check errors in body
        if question['body']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question body.')
        # check errors in options
        if question['options']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question options.')
        for option in question['options']['values']:
            if option['is_error'] is True:
                raise QuestionPaperParsingError(u'Errors in question options.')
        # check errors in text solution
        if question['text_solution']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in text solution.')
        # check errrors in ontology
        if question['ontology']['is_error'] is True:
            raise QuestionPaperParsingError(u'Errors in question ontology.')

def move_images_to_final_bucket(markup, question_files_final_bucket):
    """Finds the references to the images in the markup and figures out the S3 key of the
    temproary bucket of the images and then moves it into the final bucket.

    Keyword Arguments:
    markup -- the html markup in which images need to be found

    Response Structure
    str -- the updates markup
    """

    # parse the markup using bs and find the image tags
    soup = BeautifulSoup(markup, 'html.parser')
    img_els = soup.find_all(u'img')

    # S3 connection & buckets
    final_bucket = question_files_final_bucket

    # iterate over the image elements, copy the images to the new bucket and also change the src attribute of the images
    for el in img_els:
        src_url = el.attrs['src']
        key_name = os.path.basename(src_url)
        final_bucket.copy_key(key_name, app.config['S3_QUESTION_FILES_TEMP_BUCKET'], key_name, preserve_acl=True)
        el.attrs['src'] = ''.join(['https://', app.config['S3_QUESTION_FILES_FINAL_BUCKET'], '.s3.amazonaws.com/', key_name])

    return str(soup)


def add_questions_to_db_and_mock_test(paper_questions, comprehensions, mock_test_id):
    """This method adds the given questions (result of `parse_question`) to the DB
    and also adds them to the questions_ids attribute of the mock test row.
    """

    ## Get the mock test
    mock_test = MockTest.query.get(mock_test_id)

    ## Get the S3 buckets here (otherwise will have to make calls for every content block)
    conn = S3Connection(config.S3_ACCESS_KEY, config.S3_SECRET)
    question_files_final_bucket = conn.get_bucket(app.config['S3_QUESTION_FILES_FINAL_BUCKET'])

    ## Upload the questions to the DB if there are no errors
    added_questions = []
    comprehension_ids = {}

    print 'Number of Questions: {0}'.format(len(paper_questions))

    for question in paper_questions:
        status = dict(config.QUESTION_STATUS.items())
        status['categorized'] = '1'
        status['text_solution_added'] = '1'
        # status['proof_read_categorization'] = '1'

        # make a list of the correct options
        correct_options = []
        for i in range(len(question['options']['values'])):
            if question['options']['values'][i]['correct']:
                correct_options.append(i)

        # move the images to s3 and change the markup accordingly
        """
        question['body']['value'] = move_images_to_final_bucket(question['body']['value'], question_files_final_bucket)
        question['text_solution']['value'] = move_images_to_final_bucket(question['text_solution']['value'], question_files_final_bucket)
        for i in range(len(question['options']['values'])):
            question['options']['values'][i]['value'] = move_images_to_final_bucket(question['options']['values'][i]['value'],
                                                                                        question_files_final_bucket)
        for i in range(len(comprehensions)):
            comprehensions[i]['value'] = move_images_to_final_bucket(comprehensions[i]['value'], question_files_final_bucket)
        """

        # create a comprehension if needed or just pick up a comprehension ID
        comprehension_id = None
        if question['comprehension']:
            if comprehension_ids.get(question['comprehension_index']):
                comprehension_id = comprehension_ids[question['comprehension_index']]
            else:
                comp_ = comprehensions[question['comprehension_index']]
                comprehension = Comprehension.create(comp_['value'])
                db.session.add(comprehension)
                db.session.commit()
                comprehension_id = comprehension.id
                comprehension_ids[question['comprehension_index']] = comprehension.id

        # create the question in the DB
        question_data = {
            'content': question['body']['value'],
            'status': status,
            'all_options': [option['value'] for option in question['options']['values']],
            'correct_options': correct_options,
            'ontology_id': question['ontology']['value'][-1],
            'average_time': int(question['attributes']['average_time']['value']),
            'nature': question['attributes']['nature']['value'],
            'difficulty': question['attributes']['difficulty']['value'],
            'type': question['attributes']['type']['value'],
            'text_solution': question['text_solution']['value'],
            'text_solution_by_type': 1,
            'text_solution_by_id': app.config['AUTO_UPLOAD_DTP_ID'],
            'comprehension_id': comprehension_id
        }
        question_ = Question.create(**question_data)
        added_questions.append([question_, question['ontology']['value']])

        # create the attached text solution submission row in the db too
        solution_submission_params = {
            'submitted_by_type': 3,
            'submitted_by_id': app.config['AUTO_UPLOAD_TEACHER_ID'],
            'question_id': question_.id,
            'solution_type': 'text',
            'solution': question['text_solution']['value'],

        }
        SolutionSubmission.create(**solution_submission_params)

        # create the attached category submission row in the db too
        last_ontology_obj = Ontology.query.get(question_data['ontology_id'])
        category_submission_params = {
            'submitted_by_type': 3,
            'submitted_by_id': app.config['AUTO_UPLOAD_TEACHER_ID'],
            'question_id': question_.id,
            'ontology': last_ontology_obj.absolute_path,
            'nature': question_data['nature'],
            'type': question_data['type'],
            'difficulty': question_data['difficulty'],
            'average_time': question_data['average_time']
        }
        CategorySubmission.create(**category_submission_params)

    ## Add the questions to the mock Test
    mock_test_questions = {}
    order = -1
    for question,ontology in added_questions:
        subject_id = ontology[0]
        if str(subject_id) not in mock_test_questions:
            print str(subject_id)
            order = order + 1
            mock_test_questions.update({str(subject_id): {'order': order, 'q_ids': [question.id]}})
            continue
        if str(subject_id) in mock_test_questions:
            mock_test_questions[str(subject_id)]['q_ids'].append(question.id)
            continue

    print mock_test_questions.keys()

    ## Add the `mock_test_questions` to the mock test
    mock_test.question_ids = json.dumps(mock_test_questions)
    db.session.add(mock_test)
    db.session.commit()

    return True

def add_paper_to_db(archive, mock_test_id):
    """This method will parse all the questions from the paper using `parse.parse_paper` method
    and then upload the questions to the DB. It will also add the questions added to the DB to the
    mock test with the given ID.

    Keyword Arguments:
    archive -- the file like object of the zip archive of the paper.
    mock_test_id -- the id of the mock test in which the added questions need to be added.
    """

    ## Get the parsed questions using `parse.parse_paper`
    paper_questions = parse_paper(archive)

    # Check if the given mock test ID exists
    if not mock_test:
        raise QuestionPaperParsingError(u'No mock test with the given mock test ID ({0}) exists.'.format(mock_test_id))

    return mock_test_questions
