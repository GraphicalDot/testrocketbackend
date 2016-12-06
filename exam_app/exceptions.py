# -*- coding: utf-8 -*-


class TestAppException(Exception):
    pass


# authentication / authorization exceptions


class AuthenticationFailure(TestAppException):
    http_response_code = 401
    error_code = 1001
    message = "Username/Password are not provided or incorrect"


class UnknownUserType(TestAppException):
    http_response_code = 401
    error_code = 1002
    message = "Unrecognized user type"


class UnauthorizedToAccess(TestAppException):
    http_response_code = 401
    error_code = 1003
    message = "Not allowed to make this request"
    

# registration exceptions

class EmailAlreadyRegistered(TestAppException):
    http_response_code = 400
    error_code = 1101
    message = "Email already registered. Use a different email"


class MobileNoAlreadyRegistered(TestAppException):
    http_response_code = 400
    error_code = 1102
    message = "Mobile number registered. Use a mobile number"


class UsernameAlreadyRegistered(TestAppException):
    http_response_code = 400
    error_code = 1103
    message = "Username registered. Use a username"


class BatchNameAlreadyTaken(TestAppException):
    http_response_code = 400
    error_code = 1104
    message = "A batch already exists with this name."


# Invalid ids provided


class InvalidOntologyNodeId(TestAppException):
    http_response_code = 400
    error_code = 2001
    message = "Invalid node id for ontology node"


class InvalidMockTestId(TestAppException):
    http_response_code = 400
    error_code = 2002
    message = "Mock Test with provided id does not exist"


class InvalidDataOperatorId(TestAppException):
    http_response_code = 400
    error_code = 2003
    message = "Data Operator with provided id does not exist"


class InvalidTeacherId(TestAppException):
    http_response_code = 400
    error_code = 2004
    message = "Teacher with provided id does not exist"


class InvalidInternId(TestAppException):
    http_response_code = 400
    error_code = 2005
    message = "Intern with provided id does not exist"


class InvalidStudentId(TestAppException):
    http_response_code = 400
    error_code = 2006
    message = "Student with provided id does not exist"


class InvalidInstituteId(TestAppException):
    http_response_code = 400
    error_code = 2007
    message = "Institute with provided id does not exist"


class InvalidQuestionId(TestAppException):
    http_response_code = 400
    error_code = 2008
    message = "Question with provided id does not exist"


class InvalidAttemptedMockTestId(TestAppException):
    http_response_code = 400
    error_code = 2009
    message = "Attempted Mock Test with provided id does not exist"


class InvalidBatchId(TestAppException):
    http_response_code = 400
    error_code = 2008
    message = "Batch with provided id does not exist"

# ontology restriction exceptions


class CannotDeleteNonLeafOntologyNode(TestAppException):
    http_response_code = 500
    error_code = 3001
    message = "Invalid parent id for ontology node"


class CannotUpdateTheoryOfNonLeafOntologyNode(TestAppException):
    http_response_code = 500
    error_code = 3002
    message = "Invalid parent id for ontology node"


class AtleastOneTargetExamNeededForOntologyRootNode(TestAppException):
    http_response_code = 500
    error_code = 3003
    message = "At least One Target Exam Needed For Ontology Root Node"


# disallowed values exceptions


class UnknownTargetExam(TestAppException):
    http_response_code = 400
    error_code = 4001
    message = "Unknown target exam"


class UnknownOntologyNodeType(TestAppException):
    http_response_code = 400
    error_code = 4002
    message = "Unknown ontology node type"


class UnknownOntologyNodeClass(TestAppException):
    http_response_code = 400
    error_code = 4003
    message = "Unknown ontology node class"


class UnAcceptableFileType(TestAppException):
    http_response_code = 400
    error_code = 4004
    message = "The file type cannot be uploaded. Choose a different file"


class UnAcceptableEmail(TestAppException):
    http_response_code = 400
    error_code = 4005
    message = "The email is not valid. Provide a different email"


class UnAcceptableVideoUrl(TestAppException):
    http_response_code = 400
    error_code = 4006
    message = "The url is not valid. Provide a youtube url"


class PaymentPlanLimitReached(TestAppException):
    http_response_code = 400
    error_code = 4007
    message = "You have attempted the maximum number of tests permitted under your payment plan"


class MockTestTestAlreadyAttempted(TestAppException):
    http_response_code = 400
    error_code = 4008
    message = "You have already attempted this mock test."


class BatchNotEmpty(TestAppException):
    http_response_code = 400
    error_code = 4009
    message = "The batch still has students. Move students belonging to this batch to some other batch"
    
class ArchiveS3KeyDoesNotExist(TestAppException):
    http_response_code = 400
    error_code = 4010
    message = "The S3 key with the given name does not exist."

class QuestionUploadSetMockSetNotEmpty(TestAppException):
    http_response_code = 400
    error_code = 4011
    message = "The mock selected already has some questions present in it. Select an empty mock test."

class OverallQuestionParsingError(TestAppException):
    http_response_code = 400
    error_code = 4012
    mesage = "There are some errors in the archive you uploaded. Please check."

class InvalidUploadSetId(TestAppException):
    http_response_code = 400
    error_code = 4013
    message = "Invalid upload set ID."

class UploadSetAlreadyAdded(TestAppException):
    http_response_code = 400
    error_code = 4014
    message = "Upload set has alrady been added."
    
class UploadSetHasErrors(TestAppException):
    http_response_code = 400
    error_code = 4013
    message = "Upload set has some errors."
