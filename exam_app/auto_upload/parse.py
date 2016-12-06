# -*- coding: utf-8 -*-
import zipfile

from bs4 import BeautifulSoup
from boto.s3.connection import S3Connection

from exam_app import app
from exam_app.auto_upload import config
from exam_app.auto_upload.helpers import (remove_extra_spaces, check_similarity, get_ontology_ids, clean_content_block, clone,
                                            check_if_option_is_correct)
from exam_app.auto_upload.exceptions import (ZipArchiveStructureError, BeautifulSoupParsingError, QuestionAttributesParsingError,
                                                OntologyParsingError, ContentParsingError)

def parse_paper(zip_archive):
    """Parses a question paper from a zip archive. This archive comprises
    of the output when a word file is saved as a "Wed Page".

    Note: The zip archive structure is assumed to be something like this:
          -- paper.html
          -- paper_files/image001.png
          -- paper_files/image002.png
          -- paper_files/image003.png

    Keyword Arguments:
    zip_archive -- the file-like object of the archive. this will be unarchived using `zipfile`

    Final Response:
    {
        'is_overall_error': False,
        'overall_errors': [] # list of exceptions if they exist. error text can be access using the `message` attribute.
        'questions': [
            { # will contain the output as described in `parse_question` },
            {}, {}, {}
        ]
    }
    """

    ## Unzip the archive
    archive = zipfile.ZipFile(zip_archive)

    # Final response structure
    final_response = {
        'is_overall_error': False,
        'overall_errors': [],
        'questions': [],
        'comprehensions': []
    }

    ## Verify the contents of the archive

    # check only one html file exists in the archive
    html_files = [f_name for f_name in archive.namelist() if 'html' in f_name and '/' not in f_name]
    if len(html_files) > 1:
         e = ZipArchiveStructureError(u'More than 1 HTML files exist in this archive.')
         final_response['is_overall_error'] = True
         final_response['overall_errors'].append(e)
         return final_response
    if len(html_files) == 0:
        e = ZipArchiveStructureError(u'No HTML files exist in this archive.')
        final_response['is_overall_error'] = True
        final_response['overall_errors'].append(e)
        return final_response
    html_file = html_files[0]

    # check that the files directory exists
    f_dir_files = filter(lambda f: html_file.replace(u'.html', '') + "_files" in f, archive.namelist())
    if len(f_dir_files) == 0:
        e = Exception(u'No files directory exists in this archive.')
        final_response['is_overall_error'] = True
        final_response['overall_errors'].append(e)
        return final_response

    ## Parse the html file using BeautifulSoup
    try:
        html_file = archive.open(html_file)
        soup = BeautifulSoup(html_file.read().decode(u'utf-8', 'ignore'), 'html.parser')
        # soup = BeautifulSoup(html_file.read(), 'html.parser')
    except Exception as e:
        e = BeautifulSoupParsingError(u'The HTML file cannot be parsed properly.')
        final_response['is_overall_error'] = True
        final_response['overall_errors'].append(e)
        return final_response

    ## Extract question objects by finding all the tables in the html file
    question_tables = soup.find_all(u'table')
    if len(question_tables) == 0:
        e = Exception(u'No questions were found in the HTML file.')
        final_response['is_overall_error'] = True
        final_response['overall_errors'].append(e)
        return final_response

    ## Get the S3 bucket to upload images to. Will not have to get images againa nd again this way
    conn = S3Connection(app.config['S3_ACCESS_KEY'], app.config['S3_SECRET'])
    question_files_bucket = conn.get_bucket(app.config['S3_QUESTION_FILES_TEMP_BUCKET'])

    ## Loop over all the questions and get the parsed results and errors
    for question_table in question_tables:
        question_type = check_if_comprehension_or_normal(question_table)
        if question_type == 1:
            question = parse_normal_question(question_table, archive, question_files_bucket)
            final_response['questions'].append(question)
        else:
            questions = parse_comprehension_question(question_table, archive, question_files_bucket)
            final_response['comprehensions'].append(questions['comprehension'])
            comprehension_index = len(final_response['comprehensions']) - 1
            for question in questions['questions']:
                question['comprehension_index'] = comprehension_index
                final_response['questions'].append(question)

    #question = parse_question(question_tables[2], archive, question_files_bucket)
    #final_response['questions'].append(question)

    ## Return the response
    return final_response

def parse_comprehension_question(question_table, archive, question_files_bucket):
    """Parsed a single table (comprising of multiple questions associated with one
    comprehension given at the top of the table) and returns all the data.

    Keyword Arguments:
    question_table -- the table extracted by BeautifulSoup from the parsed html page.
    archive -- zipfile archive
    question_files_bucket -- S3 bucket where the question files will be stored

    Response Structure:
    {
        'questions': [
            {#this dict will be same as the response structure of `parse_normal_question`},
            {}, {}, {}
        ],
        'comprehension': {
            'is_error': False,
            'value': 'Actual comprehension body goes here.',
            'errors': ['Error #1', 'Error #2']
        }
    }
    """

    ## Construct the final response
    final_response = {
        'questions': [],
        'comprehension': {}
    }

    ## get the comprehension body
    comprehension = get_question_comprehension(clone(question_table), archive, question_files_bucket)
    final_response['comprehension'] = comprehension

    ## Seperate the different questions in the table
    seperated_questions = {}
    table_rows = question_table.find_all(u'tr')[2:]
    index = -1
    for row in table_rows:

        row_text = row.text.strip().lower().replace(u'\n', '').replace(u'\r', '')

        if 'testrocket' in row_text and 'question' in row_text:
            index = index +1
            seperated_questions[index] = [row]
        else:
            seperated_questions[index].append(row)

    ## Construct BS tags for every question
    question_tables = []
    for index, question in seperated_questions.items():
        soup = BeautifulSoup(u'<table></table>', 'html.parser')
        table_tag = soup.find(u'table')
        for i in range(len(question)):
            if i != 0:
                table_tag.append(question[i])
        question_tables.append(table_tag)

    ## Parse the data of the indivual questions
    questions = []
    for table in question_tables:
        question = {'comprehension': True}
        # Get the question attributes
        attributes = get_question_attributes(clone(table))
        question['attributes'] = attributes
        # Get the ontology
        ontology = get_ontology(clone(table))
        question['ontology'] = ontology
        ## Get the question body
        body = get_question_body(clone(table), archive, question_files_bucket)
        question['body'] = body
        # Get the options
        options = get_options(clone(table), archive, question_files_bucket)
        question['options'] = options
        ## Get the text solution
        text_solution = get_text_solution(clone(table), archive, question_files_bucket)
        question['text_solution'] = text_solution

        questions.append(question)

    final_response['questions'] = questions


    ## Return the final response
    return final_response


def parse_normal_question(question_table, archive, question_files_bucket):
    """Parses a single table (comprising of a single question) extracted by BeautifulSoup
    and returns all the relevant parsed attributes and the errors got while parsing them.

    Keyword Arguments:
    question_table -- the tables extracted by BeautifulSoup from the parsed html page.

    Response Structure:
    {
        'comprehension': False,
        'attributes': {
            'is_error': False,
            'errors': [],
            'nature': {'value': 1, 'errors': [], 'is_error': False}
            'difficulty': {'value': 1, 'errors': [], 'is_error': False}
            'type': {'value': 1, 'errors': [], 'is_error': False}
            'average_time': {'value': 1, 'errors': [], 'is_error': False}
        },

        'body': {
            'is_error': False,
            'value': 'Actual question body comes here.',
            'errors': ['Error #1', 'Error #2']
        },

        'options': {
            'is_error': False,
            'errors': [],
            'values': [
                {
                    'is_error': False,
                    'value': 'Actual HTML of the option #1 comes here.',
                    'errors': [],
                    'correct': True
                }, {}, {}, {}
            ],
        },

        'text_solution': {
            'is_error': False,
            'value': 'HTMl of the text solution comes here.',
            'errors': [],
        },

        ontology: {
            'value': [], # ontology ordered list of ids
            'errors': [],
            'is_error': False
        }

    }

    Notes about the response structure:

    1. The `value` under every section contains the actual value which will be used in the system.
    2. The `errors` keys in every section correspond to the errors which are caught while parsing that exception.
    3. `parsing_error` in the `attributes` key indicates that the complete attributes could not be parsed correctly.
    """

    ## Construct the final response
    final_response = {
        'comprehension': False,
        'attributes': {},
        'ontology': {},
        'body': {},
        'options': {}
    }

    ## Get the question attributes
    attributes = get_question_attributes(clone(question_table))
    final_response['attributes'] = attributes

    ## Get the ontology
    ontology = get_ontology(clone(question_table))
    final_response['ontology'] = ontology

    ## Get the question body
    body = get_question_body(clone(question_table), archive, question_files_bucket)
    final_response['body'] = body

    ## Get the options
    options = get_options(clone(question_table), archive, question_files_bucket)
    final_response['options'] = options

    ## Get the text solution
    text_solution = get_text_solution(clone(question_table), archive, question_files_bucket)
    final_response['text_solution'] = text_solution

    ## Return the final response
    return final_response

def check_if_comprehension_or_normal(question_table):
    """Checks if the question(s) in the given question table are of the normal type
    or they are a set of questions (comprehension).

    Keyword Arguments:
    question_table -- the question table extracted using BS.

    Response Structure:
    int -- 1 for normal, 2 for comprehension
    """

    question_table = clone(question_table)

    # comprehension table have comprehension written in the first row
    # which is not divided into any column. so check for these condition.
    first_row = question_table.find_all(u'tr')[0]
    if len(first_row.find_all(u'td')) < 4 and 'comprehension' in first_row.text.strip().lower():
        return 2
    else:
        return 1


def get_question_comprehension(question_table, archive, question_files_bucket):
    """Returns the question comprehension."""

    ## Construct the final response
    final_response = {
        'is_error': False,
        'value': None,
        'errors': []
    }

    ## Extract the comprehension text from the question table
    try:
        comprehension = question_table.find_all(u'tr')[1]
    except IndexError:
        e = ContentParsingError(u'Comprehension was not found.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    ## Try getting the comprehension text using `clean_content_block`
    try:
        comprehension = clean_content_block(comprehension, 'comprehension', archive, question_files_bucket)
    except Exception as e:
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response
    final_response['value'] = comprehension # if not error is generated

    return final_response


def get_text_solution(question_table, archive, question_files_bucket):
    """Returns the question options after parsing it from the question tabled passed.

    Keyword Arguments:
    question_table -- the question table extracted from BS.

    Response Structure:
    -- Refer to the `text_solution` section in the response structure of `parse_question` function
    """

    ## Construct the final response
    final_response = {
        'is_error': False,
        'value': None,
        'errors': []
    }

    ## Figure out if it is the last row of the table or the second last
    ## Sometimes word adds an empty <tr> with height=0
    empty_tr = question_table.find(u"tr", {"height": "0"})
    last_row = False
    if empty_tr:
        last_row = True

    ## Extract the text solution from the question table
    try:
        if last_row:
            solution = question_table.find_all(u'tr')[-2]
        else:
            solution = question_table.find_all(u'tr')[-1]
    except IndexError:
        e = ContentParsingError(u'Question solution was not found.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    ## Try getting the text solution from `clean_content_block`
    try:
        text_solution = clean_content_block(solution, 'text_solution', archive, question_files_bucket)
    except Exception as e:
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response
    final_response['value'] = text_solution # if not error is generated

    return final_response


def get_options(question_table, archive, question_files_bucket):
    """Returns the question options after parsing it from the question tabled passed.

    Keyword Arguments:
    question_table -- the question table extracted from BS.

    Response Structure:
    -- Refer to the `options` section in the response structure of `parse_question` function
    """

    ## Construct the final response
    final_response = {
        'values': [],
        'errors': [],
        'is_error': False
    }

    ## Extract the options from the question table and raise error if length of options is less than 4
    options_ = question_table.find_all(u'tr')[4:]
    options = []
    for opt in options_:
        if len(opt.find_all(u'td')) >= 2:
            try:
                opt_label = opt.find_all(u'td')[0].text.strip().replace(u'(correct)', '')
                int(opt_label)
                options.append(opt)
            except ValueError:
                continue
        else:
            continue

    if len(options) < 4:
        e = ContentParsingError(u'Less than 4 options exist for this question.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    ## Extract the options and append to the final result
    for opt in options:
        try:
            opt_ = clean_content_block(opt, 'question_option', archive, question_files_bucket)
            correct = check_if_option_is_correct(opt)
            final_response['values'].append({
                'is_error': False,
                'value': opt_,
                'errors': [],
                'correct': correct
            })
        except Exception as e:
            final_response['values'].append({
                'is_error': True,
                'value': None,
                'correct': None,
                'errors': [e]
            })

    return final_response

def get_question_body(question_table, archive, question_files_bucket):
    """Returns the question body after parsing it from the question table passed.

    Keyword Arguments:
    question_table -- the question table extracted from BS.

    Response Structure:
    -- Refer to the `body` section in the response structure of `parse_question` function
    """

    ## Construct the final response
    final_response = {
        'is_error': False,
        'value': None,
        'errors': []
    }

    ## Extract the question body from the question table
    try:
        body = question_table.find_all(u'tr')[3]
    except IndexError:
        e = ContentParsingError(u'Question body was not found.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    ## Try getting the question body from `clean_content_block`
    #try:
    question_body = clean_content_block(body, 'question_body', archive, question_files_bucket)
    #except Exception as e:
    #    final_response['is_error'] = True
    #    final_response['errors'].append(e)
    #    return final_response
    final_response['value'] = question_body # if not error is generated

    return final_response

def get_ontology(question_table):
    """Returns the list of ontology IDs in a list in ordered fashion by extracting the ontology
    from the question table extracted by BeautifulSoup.

    Keyword Arguments:
    question_table -- Same as `parse_question`

    Response Structure:
    -- Refer to the `ontology` section in the response structure of `parse_question` function
    """

    ## Construct the final response
    final_response = {
        'value': [],
        'is_error': False,
        'errors': []
    }

    ## Get the ontology row from the table
    try:
        ontology_row = question_table.find_all(u'tr')[2]
    except IndexError:
        e = OntologyParsingError(u'Ontology row in the question table does not exist.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    # check if a minimum of two $$ (delimeters) exist in the ontology
    ontology_text = remove_extra_spaces(ontology_row.text)
    ontology_text = ontology_text.replace(u'  ', ' ')
    if ontology_text.count(u'$$') < 2:
        e = OntologyParsingError(u'A minimum of two $$ delimeters do not exist.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    # get ontology in text form
    ontology_text = [node.strip() for node in ontology_text.split(u'$$')]

    # get the ids of ontology nodes
    print ontology_text
    ontology = get_ontology_ids(ontology_text)

    return ontology


def get_question_attributes(question_table):
    """Returns a dictionary of all the question attributes.

    Keyword Argument:
    question_table -- Same as `parse_question`

    Response Structure:
    -- Refer to the `attributes` section in the response structure of `parse_question` function.
    """

    ## Construct the final response dict
    final_response = {
        'is_error': False,
        'errors': [],
        'nature': {'value': None, 'errors': [], 'is_error': False},
        'difficulty': {'value': None, 'errors': [], 'is_error': False},
        'type': {'value': None, 'errors': [], 'is_error': False},
        'average_time': {'value': None, 'errors': [], 'is_error': False}
    }

    # get the attributes heading & attributes values rows from the table (first two rows)
    try:
        attr_heading_row = question_table.find_all(u'tr')[0]
        attr_values_row = question_table.find_all(u'tr')[1]
    except IndexError as e:
        e = QuestionAttributesParsingError(u'Attribute heading/values row was not present.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response


    # check if both rows have 4 `td` elements both
    if len(attr_heading_row.find_all(u'td')) != 4:
        e = QuestionAttributesParsingError(u'The exact number of attribute headings are not present.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    if len(attr_values_row.find_all(u'td')) != 4:
        e = QuestionAttributesParsingError(u'The exact number of attribute values are not present.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    # check if the attribute headings are correct
    attr_headings = set([heading.text.strip().lower() for heading in attr_heading_row.find_all(u'td')])
    if attr_headings != set([heading.lower() for heading in config.QUESTION_ATTRIBUTES_NAMES]):
        e = QuestionAttributesParsingError(u'Attribute headings are not correct.')
        final_response['is_error'] = True
        final_response['errors'].append(e)
        return final_response

    # list of attribute values `td` elements
    attr_values_tds = attr_values_row.find_all(u'td')

    # extract nature
    nature = remove_extra_spaces(attr_values_tds[0].text)
    for index, value in config.QUESTION_NATURE.items():
        if check_similarity(nature, value):
            final_response['nature']['value'] = index
    if final_response['nature']['value'] is None:
        e = QuestionAttributesParsingError(u'The question nature could not be recognized.')
        final_response['nature']['is_error'] = True
        final_response['nature']['errors'].append(e)

    # extract type
    q_type = remove_extra_spaces(attr_values_tds[1].text)
    for index, value in config.QUESTION_TYPE.items():
        if check_similarity(q_type, value):
            final_response['type']['value'] = index
    if final_response['type']['value'] is None:
        e = QuestionAttributesParsingError(u'The question type could not be recognized.')
        final_response['type']['is_error'] = True
        final_response['type']['errors'].append(e)
        return final_response

    # extract difficulty
    difficulty = remove_extra_spaces(attr_values_tds[2].text)
    difficulty = [i.strip() for i in difficulty.split(u'/')][0]
    if difficulty not in config.QUESTION_DIFFICULTY_LEVEL:
        e = QuestionAttributesParsingError(u'The question difficulty could not be recognized.')
        final_response['difficulty']['is_error'] = True
        final_response['difficulty']['errors'].append(e)
        return final_response
    else:
        final_response['difficulty']['value'] = difficulty

    # extract time
    q_time = remove_extra_spaces(attr_values_tds[3].text)
    if q_time not in config.QUESTION_AVERAGE_TIME:
        e = QuestionAttributesParsingError(u'The question time could not be recognized.')
        final_response['average_time']['is_error'] = True
        final_response['average_time']['errors'].append(e)
        return final_response
    else:
        final_response['average_time']['value'] = q_time

    # return the final response
    return final_response
