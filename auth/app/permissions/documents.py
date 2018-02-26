from umongo import Document, validate
from umongo.fields import StringField

from app import app


instance = app.config["LAZY_UMONGO"]


@instance.register
class Permission(Document):
    codename = StringField(
        unique=True,
        allow_none=False,
        required=True,
        validate=validate.Regexp(
            r'^[a-z\-\.]+$',
            error="Field value can contain only 'a'-'z', '.', '-' characters."
        )
    )
    description = StringField(allow_none=True)

    class Meta:
        indexes = ['$codename', ]
