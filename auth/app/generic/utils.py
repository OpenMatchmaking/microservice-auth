ERROR_FIELD_NAME = 'details'


def wrap_error(message):
    return {ERROR_FIELD_NAME: message}
