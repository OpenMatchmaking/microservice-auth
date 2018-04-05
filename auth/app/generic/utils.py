AUTHORIZATION_ERROR = "AuthorizationError"
NOT_FOUND_ERROR = "NotFoundError"
TOKEN_ERROR = "TokenError"
HEADER_ERROR = "HeaderError"
VALIDATION_ERROR = "ValidationError"

CONTENT_FIELD_NAME = 'content'
ERROR_FIELD_NAME = 'error'
EVENT_FIELD_NAME = 'event-name'


def wrap_error(type, message):
    if isinstance(message, str) and not message.endswith('.'):
        message = message + '.'
    return {
        ERROR_FIELD_NAME: {
            "type": type,
            "message": message
        }
    }
