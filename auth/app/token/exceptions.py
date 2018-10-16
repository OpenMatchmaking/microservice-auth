from sage_utils.constants import TOKEN_ERROR, AUTHORIZATION_ERROR, HEADER_ERROR
from sage_utils.wrappers import Response


class BaseTokenException(Exception):
    error_type = TOKEN_ERROR
    message = "Occurred an error during processing token."

    def __init__(self, message=message):
        super(BaseTokenException, self).__init__(message)

    @property
    def details(self):
        return Response.from_error(self.error_type, self.message).data


class MissingAccessToken(BaseTokenException):
    error_type = AUTHORIZATION_ERROR
    message = "An access token isn't set in request."
