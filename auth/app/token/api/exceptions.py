from sanic.exceptions import SanicException

from app.generic.utils import wrap_error


class BaseTokenException(SanicException):
    status_code = 400
    message = "Occurred an error during processing token."

    def __init__(self, message=message):
        super().__init__(message)

    @property
    def details(self):
        return wrap_error(self.message)


class MissingAuthorizationHeader(BaseTokenException):
    message = "Authorization header isn't set in request."


class InvalidHeaderPrefix(BaseTokenException):
    prefix = None
    message = "Before the token necessary to specify the `{prefix}` prefix."

    def __init__(self, message=message, prefix=''):
        super().__init__(message)
        self.prefix = prefix

    @property
    def details(self):
        message = self.message.format(prefix=self.prefix)
        return wrap_error(message)
