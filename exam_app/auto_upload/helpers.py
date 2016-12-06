# -*- coding: utf-8 -*-
import mimetypes, os
from uuid import uuid4

from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag, Comment
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from exam_app.auto_upload.exceptions import OntologyParsingError, ContentParsingError
from exam_app.auto_upload import config
from exam_app.models.ontology import Ontology
from exam_app import app

# enable the app context to actually use the SQLAlchemy models.
ctx = app.test_request_context()
ctx.push()

def clone(el):
    if isinstance(el, NavigableString):
        return type(el)(el)

    copy = Tag(None, el.builder, el.name, el.namespace, el.nsprefix)
    # work around bug where there is no builder set
    # https://bugs.launchpad.net/beautifulsoup/+bug/1307471
    copy.attrs = dict(el.attrs)
    for attr in ('can_be_empty_element', 'hidden'):
        setattr(copy, attr, getattr(el, attr))
    for child in el.contents:
        copy.append(clone(child))
    return copy

def check_index_exists(index, _list):
    """Check if a particular index on a list exists.

    Keyword Arguments:
    index -- index number to check
    _list -- list on which index number's existence needs to be checked.

    Response:
    boolean.
    """
    try:
        _list[index]
    except IndexError:
        return False

    return True

def remove_extra_spaces(string):
    """Removes the extra spaces from a given string. These space charecters are the ones
    list in config.BS_EXTRA_SPACES_NOT_NEEDED.

    Keyword Arguments:
    string -- the string from which the extra spaces need to be removed.
    """

    for extra in config.BS_EXTRA_SPACES_NOT_NEEDED:
        string = string.replace(extra, '')
    return string.strip()


def check_similarity(value1, value2):
    """Checks if the similarity of two strings is above the threshold
    defined in `config.QUESTION_ATTRIBUTES_SIMILARITY_THRESHOLD`

    Keyword Arguments:
    value1 -- string 1 to compare
    value2 -- string 2 to compare
    """

    if fuzz.ratio(value1, value2) >= config.QUESTION_ATTRIBUTES_SIMILARITY_THRESHOLD:
        return True
    return False

def remove_extra_tags(tag):
    """Removes the extra tags listed in `config.BS_EXTRA_TAGS` from the given BS tag.

    Note: The tags are removed using `tag.decompose()` method of BS.

    Keyword Arguments:
    tag -- the BS tag from which extra tags need to be removed.

    Response Structure:
    Returns nothing. The BS tag is edited in place itself.
    """

    # removing extra tags
    for tag_extra in config.BS_EXTRA_TAGS:
        extras = tag.find_all(tag_extra)
        [i.decompose() for i in extras]

    # removing comments
    for tag_ in tag(text=lambda text: isinstance(text, Comment)):
        tag_.extract()


def check_equation_start(tag):
    """Checks if there is a equation starting tag as a part of the current tag. The
    equation starting tag will be in escaped format so `tag.text` is used.

    Equation starting tag looks like <math display='block'>

    Keyword Arguments:
    tag -- the tag in which equation starting needs to be checked.
    """

    if 'math' in tag.text and "display" in tag.text and "block" in tag.text:
        return True
    elif '<math>' in tag.text:
        return True
    else:
        return False

def check_equation_end(tag):
    """Same as `check_equation_start` but to check the ending of the equation.

    Equation end tag looks like `</math>`

    Keyword Arguments:
    tag --  the tag in which equation ending needs to be checked.
    """

    return '</math>' in tag.text

def clean_equation_tag(tag):
    """Does some cleaning up of the equation tags. Removed un-needed elements.

    Keyword Arguments:
    tag -- the equation tag to be cleaned up.

    Response Structure:
    None. The tag is modified in place.
    """

    for t in tag.find_all():
        if t.attrs.get('style') and 'mso-spacerun' in t.attrs['style']:
            t.decompose()


def get_ontology_ids(ontology_list):
    """Takes a list of ordered ontology nodes in textual form and returns the
    corresponding IDs of the same.

    If there is an error then also returns a list of exceptions of the errors or
    if none exist the errors list is empty.

    Keyword Arguments:
    ontology_list -- ordered list of ontology nodes

    Response Structure:
    {
        'value': [1,2,3,5],
        'is_error': False,
        'errors': []
    }
    """

    ## Construct the final response
    final_response = {
        'value': [],
        'is_error': False,
        'errors': []
    }

    ## Look up for ontology
    ontology = []
    for node_name in ontology_list:
        node = Ontology.query.filter_by(name=node_name).first()
        if node is None:
            e = OntologyParsingError(u"No node with the value {0} exists.".format(node_name))
            final_response['errors'].append(e)
            final_response['is_error'] = True
        else:
            final_response['value'].append(node.id)

    ## Check if the last node of the ontology is a leaf node
    if len(final_response['value']) > 0:
        last_node_id = final_response['value'][-1]
        if not Ontology.is_leaf_node(last_node_id):
            e = OntologyParsingError(u"The last node of the ontology given is not a leaf node. Node ID: {0}".format(last_node_id))
            final_response['errors'].append(e)
            final_response['is_error'] = True

    ## Return the final response
    if len(final_response['errors']) > 0:
        final_response['value'] = None
        return final_response
    else:
        return final_response

def upload_images_to_s3(markup, archive, question_files_bucket):
    """Uploads all the images referenced in the markup to S3. Exracts the
    images from the '***_files' directory in the zip archive.

    Keyword Arguments:
    markup -- the string markup whose images need to be uploaded to s3.
    archive -- the archive object as returned by zipfile.
    """

    ## Create a BS object from the markup
    soup = BeautifulSoup(markup, 'html.parser')

    ## Find all the image objects
    imgs = soup.find_all('img')

    ## Iterate over all the images, get the file path, upload the file to S3 and change the attribute to point to the S3 hosted image
    bucket = question_files_bucket
    for img in imgs:
        path = img.attrs['src']
        img_file = archive.open(path)
        img_s3 = Key(bucket)
        img_s3.key = ''.join([str(uuid4()), '_', os.path.basename(path)])
        img_s3.content_type = mimetypes.guess_type(path)[0]
        img_s3.set_contents_from_string(img_file.read())
        img_s3.set_acl('public-read')
        img_url = ''.join(['https://', app.config['S3_QUESTION_FILES_TEMP_BUCKET'], '.s3.amazonaws.com/', img_s3.key])
        img.attrs['src'] = img_url

    return str(soup)


def check_if_option_is_correct(tag):
    """Checks if the given option in the tag is a correct one or not.
    If it is then returns True or returns False.

    Keyword Argument:
    tag -- the tag for which the processing needs to happen.

    Response Structure:
    boolean
    """

    option_label = tag.find_all('td')[0]
    return '(correct)' in option_label.text


def do_final_cleanup2(tag, _type, archive, question_files_bucket, upload_images=True):

    # change all the math tags display attribute to inline
    math_els = tag.find_all('script')

    # divide the contents of the tag and remove the empty lines
    contents = []
    if _type == 'text_solution' or _type == 'question_body' or _type == 'comprehension':
        contents = tag.find('td').contents
    elif _type == 'question_option':
        contents = tag.find_all('td')[1].contents
    contents = [elem for elem in contents if type(elem) is not NavigableString]

    # divide the contents according to delimeters
    starting_delimeter_found = False
    seperated_contents = []
    for elem in contents:
        elem_ = str(elem)
        # the starting and ending are in the same element
        if elem_.count('%^&amp;*()') == 2:
            seperated_contents.append([])
            seperated_contents[-1].append(elem)
            continue
        # the starting has been found but not the ending
        if elem_.count('%^&amp;*()') == 1 and starting_delimeter_found is False:
            starting_delimeter_found = True
            seperated_contents.append([])
            seperated_contents[-1].append(elem)
            continue
        # ending not found, so continue append to the last group
        if elem_.count('%^&amp;*()') == 0 and starting_delimeter_found is True:
            seperated_contents[-1].append(elem)
            continue
        # ending delimeter is found
        if elem_.count('%^&amp;*()') == 1 and starting_delimeter_found is True:
            seperated_contents[-1].append(elem)
            starting_delimeter_found = False
            continue

    # combine the seperated contents into different tags
    final_contents = []
    for content in seperated_contents:
        soup = BeautifulSoup('<p></p>', 'html.parser').find('p')
        final_contents.append(soup)
        for elem in content:
            elem_contents = elem.contents
            elem_contents = [j for j in elem_contents]
            for el in elem_contents:
                final_contents[-1].append(el)
    # return the final contents as a string
    final_contents = ''.join([str(i) for i in final_contents]).replace('%^&amp;*()', '')

    ## Upload the images to S3
    if upload_images:
        final_response = upload_images_to_s3(final_contents, archive, question_files_bucket)
    else:
        final_response = final_contents

    return final_response


def clean_content_block(tag, block_type, archive, question_files_bucket):
    """Cleans a content block of a lot of un-needed bullshit.

    All the processing that is happening in the content block:
    1. All the extra tags as listed in `config.BS_EXTRA_TAGS` are removed.
    2. Remove un-needed attributes of certain tags.

    Keyword Arguments:
    tag -- the tag that needs to be cleaned up.

    Response Structure:
    -- String form of the BS tag passed all cleaned up and pretty ;-)
    """

    tag = clone(tag)

    ## Remove un-needed tags from the current tag
    try:
        remove_extra_tags(tag)
    except:
        pass

    ## Remove some of the un-needed attributes of certain tags which are not really needed
    for t in tag.find_all():
        if not t.attrs: continue
        if t.attrs.get('class') and 'MTConvertedEquation' not in t.attrs['class']: t.attrs.pop('class')
        if t.attrs.get('id'): t.attrs.pop('id')
        if t.attrs.get('style'): t.attrs.pop('style')

    ## Find all the MathML existing in the given tag
    equations = tag.find_all('span', class_='MTConvertedEquation')

    ## Compile the MathML equations in a sorted format
    sorted_equations = {}
    current_equation_number = -1
    waiting_equation_ending = False
    for tag_ in equations:
        equation_start = check_equation_start(tag_)
        if equation_start:
            waiting_equation_ending = True
            current_equation_number += 1
            sorted_equations[str(current_equation_number)] = []
        if check_equation_end(tag_):
            waiting_equation_ending = False
        sorted_equations[str(current_equation_number)].append(tag_)

    # raise an error if we are still waiting for an equation ending. means the ending of a particular equation was never found.
    #if waiting_equation_ending:
    #    raise ContentParsingError('Ending for certain MathML equations was not found.')

    ## Compile equations distrubuted across different <p> tags as they are unescaped on the page
    ## into a single parent tag.
    for index, equations in sorted_equations.items():
        str_eq = u""
        first_eq_tag = None
        for i in range(len(equations)):
            # first equation in the list. incase the equation has a 'span' parent tag or is not the sole member
            # of a p tag it means that it is supposed to be an inline equation
            if i == 0:
                first_eq_tag = equations[0]
                str_eq = '<math display="inline">'
                #str_eq += remove_extra_spaces(equations[0].text)
                #if equations[0].parent.name == 'span' or len(equations[0].parent.contents) > 1:
                #    str_eq = str_eq.replace('block', 'inline')
            # anyother equation except the first one.
            else:
                clean_equation_tag(equations[i])
                remove_extra_tags(equations[i])
                str_eq += remove_extra_spaces(equations[i].text)

            # decompsing some shit
            # TODO: figure out what exactly is this. not very clear about this one.
            if equations[i].parent.name == 'span' and i != 0:
                equations[i].decompose()
            if equations[i].parent.name == 'p' and i != 0:
                equations[i].parent.decompose()

        # enclose equation in <script type="math/mml"></script>
        str_eq = '<script type="math/mml">' + str_eq + '</script>'

        # construct a BS tag from the newly constructed equation string and replace the first equation occurence with it.
        # also remove the rest of the equation occurences.
        eq_soup = BeautifulSoup(str_eq.replace('\n', '').replace('\r', ''), 'html.parser')
        first_eq_tag.replace_with(eq_soup.contents[0])

    final_response = do_final_cleanup2(tag, block_type, archive, question_files_bucket, upload_images=True)
    return final_response
