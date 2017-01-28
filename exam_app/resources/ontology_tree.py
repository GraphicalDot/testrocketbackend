# -*- coding: utf-8 -*-

import json

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import TestAppException
from exam_app.error_responses import get_error_response
from exam_app import app
from pprint import pprint
from flask.json import jsonify

def ontology_item_json_type(item):
    """
    Parse item for the format {'name': , 'theory': , 'parent_id': , 'target_exams': , 'type': , 'class': }

    :param item:
    :return: the parsed data or raises `ValueError`
    """

    try:
        data = json.loads(item)
    except:
        raise ValueError('Malformed JSON')

    if isinstance(data, dict):
        if 'name' in data and 'parent_id' in data:
            if isinstance(data['name'], basestring) and data['name'].strip() != '':
                if data['parent_id'] is None or isinstance(data['parent_id'], int):
                    data['theory'] = data.get('theory', None)
                    data['target_exams'] = data.get('target_exams', None)
                    data['type'] = data.get('type', None)
                    data['class'] = data.get('class', None)

                    if data['parent_id'] is None and data['target_exams'] is None:
                        # if root node and no target exams specified
                        raise ValueError("Root nodes need to have at least one target exam present")
                    if data['target_exams'] is not None:
                        if data['parent_id'] is not None:
                            raise ValueError("target exams can only be associated with root nodes")
                        if not isinstance(data['target_exams'], list):
                            raise ValueError("target exams can only be a list")
                        if not set(data['target_exams']).issubset(set(app.config['TARGET_EXAMS'].keys())):
                            raise ValueError("target exams need to be present in %s" % str(tuple(app.config['TARGET_EXAMS'].keys())))
                        if data['type'] is not None and data['type'] not in app.config['ONTOLOGY_NODE_TYPES']:
                            raise ValueError("node type need to be present in %s" % str(tuple(app.config['ONTOLOGY_NODE_TYPES'].keys())))
                        if data['class'] is not None and data['type'] not in app.config['ONTOLOGY_NODE_CLASSES']:
                            raise ValueError("node class need to be present in %s" % str(tuple(app.config['ONTOLOGY_NODE_CLASSES'].keys())))
                    return data

    raise ValueError("JSON not as expected")


node_obj = {
    'id': fields.Integer,
    'name': fields.String,
    'parent_path': fields.List(fields.Integer),
    'theory': fields.String,
    'target_exams': fields.List(fields.String),
    'type': fields.String,
    'class': fields.String(attribute='clazz')
}


class OntologyTree(AuthorizedResource):

    get_response = {
        'error': fields.Boolean(default=False),
        'nodes': fields.List(fields.Nested(node_obj))
    }

    post_response = {
        'error': fields.Boolean(default=False),
        'node': fields.Nested(node_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('get_theory', type=int, choices=[0, 1], default=1)
        args = parser.parse_args()
        nodes = Ontology.get_all_nodes_of_tree(args['get_theory'] == 1)
        pprint(nodes)
        return {'nodes': nodes}

    @marshal_with(post_response)
    def post(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('node', type=ontology_item_json_type, required=True)
        args = parser.parse_args()
        node = Ontology.create_node(name=args['node']['name'], theory=args['node']['theory'], parent_id=args['node']['parent_id'],
                                    target_exams=args['node']['target_exams'], type=args['node']['type'], clazz=args['node']['class'])
        return {'node': node, 'error': False}


from exam_app.models.ontology import Ontology
