from base import BaseSanicTestCase

from app.users.documents import User


class UserAPITestCase(BaseSanicTestCase):
    document = User
