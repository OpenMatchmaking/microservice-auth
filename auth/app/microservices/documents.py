from umongo import Document, validate
from umongo.fields import StringField, ListField, ReferenceField

from app import app
from app.permissions.documents import Permission


instance = app.config["LAZY_UMONGO"]


@instance.register
class Microservice(Document):
    name = StringField(unique=True, allow_none=False, required=True)
    version = StringField(
        unique=True,
        allow_none=False,
        required=True,
        validate=validate.Regexp(
            r'^\d+\.\d+\.\d+$',
            error="Field value must match the `major.minor.patch` version semantics."
        )
    )
    permissions = ListField(ReferenceField(Permission))

    class Meta:
        indexes = ['$name', '$version']
