# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.dialects.postgresql import ARRAY

from exam_app.models import db
from exam_app import app
from exam_app.exceptions import InvalidOntologyNodeId, CannotDeleteNonLeafOntologyNode, CannotUpdateTheoryOfNonLeafOntologyNode,\
    UnknownTargetExam, AtleastOneTargetExamNeededForOntologyRootNode, UnknownOntologyNodeType, UnknownOntologyNodeClass


class Ontology(db.Model):
    __tablename__ = 'ontology'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(app.config['NAME_MAX_LENGTH']))
    parent_path = db.Column(ARRAY(db.Integer))
    theory = db.Column(db.Text)
    target_exams = db.Column(ARRAY(db.String))
    type = db.Column(db.Enum(*app.config['ONTOLOGY_NODE_TYPES'].keys(), name='ontology_node_types_enum'))
    clazz = db.Column(db.Enum(*app.config['ONTOLOGY_NODE_CLASSES'].keys(), name='ontology_node_classes_enum'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def create_node(cls, name, theory=None, parent_id=None, target_exams=None, type=None, clazz=None):
        """
        Create a new node in the ontology tree. If no parent id is provided a root node is create

        :param name: name of the node
        :param theory: theory text of the node
        :param parent_id: id of parent node
        :param target_exams: exams the node belongs to. only applies to root nodes of ontology
        :param type: type of node
        :param clazz: class of a node
        :return: the newly created node or an exception if parent_id is invalid, or if target exam is invalid
        """
        parent_path = []
        if parent_id is not None:
            # non root node
            parent = cls.query.get(parent_id)
            if parent is None:
                raise InvalidOntologyNodeId
            else:
                parent_path = parent.parent_path
                parent_path.append(parent_id)
                # only root node can correspond to exams
                target_exams = None
        else:
            # root node
            if target_exams is None or len(target_exams) < 1:
                raise AtleastOneTargetExamNeededForOntologyRootNode
            else:
                if not set(target_exams).issubset(app.config['TARGET_EXAMS'].keys()):
                    raise UnknownTargetExam

        if type is not None:
            if type not in app.config['ONTOLOGY_NODE_TYPES']:
                raise UnknownOntologyNodeType
        if clazz is not None:
            if type not in app.config['ONTOLOGY_NODE_TYPES']:
                raise UnknownOntologyNodeClass

        node = cls(name=name, theory=theory, parent_path=parent_path, target_exams=target_exams, type=type, clazz=clazz)
        db.session.add(node)
        db.session.commit()
        return node

    @classmethod
    def is_leaf_node(cls, node_id):
        """
        Returns `True` on the truth of either of the two conditions:
        1. If the node_id provided is of leaf node or not
        2. If the node_id is of the topic node (This may or may not be a leaf node)

        :param node_id:
        :return: true/false or exception if node_id is not present
        """
        node = cls.query.get(node_id)
        if node is None:
            raise InvalidOntologyNodeId

        _is_topic_node = lambda node_obj: node_obj.type is '3'
        _is_leaf_node = lambda node_id: cls.query.filter(cls.parent_path.any(node_id)).first() is None

        if ( _is_topic_node(node) or _is_leaf_node(node_id) ):
            return True
        return False


    @classmethod
    def delete_leaf_node(cls, node_id):
        """
        Delete a leaf node. If node is a non leaf node, an exception is raised

        :param node_id:
        :return:
        """
        if cls.is_leaf_node(node_id):
            node = cls.query.get(node_id)
            db.session.delete(node)
            db.session.commit()
        else:
            raise CannotDeleteNonLeafOntologyNode

    @classmethod
    def update_node_theory(cls, node_id, theory):
        """
        Update theory text of a leaf node. If node is a non leaf node, an exception is raised

        :param node_id:
        :param theory:
        :return:
        """
        if cls.is_leaf_node(node_id):
            node = cls.query.get(node_id)
            node.theory = theory
            db.session.commit()
            return node
        else:
            raise CannotUpdateTheoryOfNonLeafOntologyNode

    @classmethod
    def get_all_children_of_node(cls, node_id, get_theory=True):
        """
        Returns a list of children nodes of a node

        :param node_id:
        :param get_theory: if True return theory also else provide a boolean `theory_exists`
        :return: a list
        """
        if get_theory:
            return cls.query.filter(cls.parent_path.any(node_id)).all()
        else:
            nodes = cls.query.filter(cls.parent_path.any(node_id)).all()
            for node in nodes:
                node.theory_exists = node.theory is not None
                del node.theory
            return nodes

    @classmethod
    def get_all_nodes_of_tree(cls, get_theory=True):
        """
        Returns a list of nodes of the tree
        :param get_theory: if True return theory also else provide a boolean `theory_exists`
        :return: a list
        """
        if get_theory:
            return cls.query.filter().all()
        else:
            nodes = cls.query.filter().all()
            for node in nodes:
                node.theory_exists = node.theory is not None
                del node.theory
            return nodes

    @property
    def absolute_path(self):
        """
        Returns the absolute path of an ontology node

        :return: a list of node_ids
        """
        path = self.parent_path[:]
        path.append(self.id)
        return path

