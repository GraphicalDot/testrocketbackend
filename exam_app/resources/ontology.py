# -*- coding: utf-8 -*-

from flask.ext.restful import reqparse, fields, marshal_with

from exam_app.resources.common import AuthorizedResource
from exam_app.exceptions import TestAppException
from exam_app.error_responses import get_error_response
from exam_app.resources.ontology_tree import ontology_item_json_type, node_obj


class Ontology(AuthorizedResource):

    get_response = {
        'error': fields.Boolean(default=False),
        'nodes': fields.List(fields.Nested(node_obj))
    }

    put_response = {
        'error': fields.Boolean(default=False),
        'node': fields.Nested(node_obj)
    }

    @marshal_with(get_response)
    def get(self, *args, **kwargs):
        nodes = OntologyModel.get_all_children_of_node(kwargs['id'])
        return {'nodes': nodes}

    @marshal_with(put_response)
    def put(self, *args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('node', type=ontology_item_json_type, required=True)
        args = parser.parse_args()
        node = OntologyModel.update_node_theory(node_id=kwargs['id'], theory=args['node']['theory'])
        return {'node': node}

    def delete(self, *args, **kwargs):
        OntologyModel.delete_leaf_node(kwargs['id'])
        return {'error': False}


from exam_app.models.ontology import Ontology as OntologyModel
