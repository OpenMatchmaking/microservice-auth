from sanic.exceptions import SanicException

from app.generic.utils import TOKEN_ERROR, AUTHORIZATION_ERROR, HEADER_ERROR, wrap_error


class BaseTokenException(SanicException):
    status_code = 400
    error_type = TOKEN_ERROR
    message = "Occurred an error during processing token."

    def __init__(self, message=message):
        super(BaseTokenException, self).__init__(message)

    @property
    def details(self):
        return wrap_error(self.error_type, self.message)


class MissingAuthorizationHeader(BaseTokenException):
    error_type = AUTHORIZATION_ERROR
    message = "Authorization header isn't set in request."


class InvalidHeaderPrefix(BaseTokenException):
    prefix = None
    error_type = HEADER_ERROR
    message = "Before the token necessary to specify the `{prefix}` prefix."

    def __init__(self, message=message, prefix=''):
        super(InvalidHeaderPrefix, self).__init__(message)
        self.prefix = prefix

    @property
    def details(self):
        message = self.message.format(prefix=self.prefix)
        return wrap_error(HEADER_ERROR, message)
