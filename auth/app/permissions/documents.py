from umongo import Document
from umongo.fields import StringField

from app import app


instance = app.config["LAZY_UMONGO"]


@instance.register
class Permission(Document):
    codename = StringField(allow_none=False, required=True)
    description = StringField(allow_none=True)

    class Meta:
        indexes = ['$codename', ]
