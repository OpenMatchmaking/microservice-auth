CONTENT_FIELD_NAME = 'content'
ERROR_FIELD_NAME = 'details'


def wrap_error(message):
    if isinstance(message, str) and not message.endswith('.'):
        message = message + '.'
    return {ERROR_FIELD_NAME: message}
