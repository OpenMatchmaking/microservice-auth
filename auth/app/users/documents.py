from umongo import Document
from umongo.fields import StringField, ListField, ReferenceField

from app import app
from app.groups.documents import Group


instance = app.config["LAZY_UMONGO"]


@instance.register
class User(Document):
    username = StringField(unique=True, allow_none=False, required=True)
    password = StringField(allow_none=False, required=True)
    groups = ListField(ReferenceField(Group))

    class Meta:
        indexes = ['$username', ]
