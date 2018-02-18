from umongo import Document
from umongo.fields import StringField, ListField, ReferenceField

from app import app
from app.groups.documents import Group
from app.users.security import hash_password, verify_password


instance = app.config["LAZY_UMONGO"]


@instance.register
class User(Document):
    username = StringField(unique=True, allow_none=False, required=True)
    password = StringField(allow_none=False, required=True)
    groups = ListField(ReferenceField(Group))

    class Meta:
        indexes = ['$username', ]

    def set_password(self, password):
        self.password = hash_password(password)

    def verify_password(self, password):
        return self.password and verify_password(password, self.password)

    async def pre_insert(self):
        self.set_password(self.password)
