from pymongo import IndexModel, TEXT
from pymongo.collation import Collation
from umongo import Instance, Document
from umongo.fields import StringField, ListField, ReferenceField

from app import app
from app.permissions.documents import Permission


instance = app.config["LAZY_UMONGO"]


@instance.register
class Group(Document):
    name = StringField(allow_none=False, required=True)
    permissions = ListField(ReferenceField(Permission))

    class Meta:
        indexes = {
            "keys": [('name', TEXT), ],
            "collation": Collation(locale="en", strength=2)
        }
