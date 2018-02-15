from umongo import Instance, Document
from umongo.fields import StringField, ListField, ReferenceField

from app import app
from app.permissions.documents import Permission


instance = app.config["LAZY_UMONGO"]


@instance.register
class Microservice(Document):
    name = StringField(unique=True, allow_none=False, required=True)
    version = StringField(allow_none=False)
    permissions = ListField(ReferenceField(Permission))

    class Meta:
        indexes = ['name', ]
