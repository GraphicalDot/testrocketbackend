# -*- coding: utf-8 -*-
class QuestionPaperParsingError(Exception):
    pass

class ZipArchiveStructureError(QuestionPaperParsingError):
    pass

class BeautifulSoupParsingError(QuestionPaperParsingError):
    pass

class QuestionAttributesParsingError(QuestionPaperParsingError):
    pass

class OntologyParsingError(QuestionPaperParsingError):
    pass

class ContentParsingError(QuestionPaperParsingError):
    pass
