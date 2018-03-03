from marshmallow import validate, validates_schema, ValidationError
from marshmallow.fields import String

from app.users.documents import User


BaseUserSchema = User.schema.as_marshmallow_schema()


class CreateUserSchema(BaseUserSchema):
    id = String(
        dump_only=True,
        description='Unique document identifier of a User.'
    )
    username = String(
        required=True,
        allow_none=False,
        description='Unique username.',
        validate=validate.Length(min=1, error='Field cannot be blank.')
    )
    password = String(
        load_only=True,
        required=True,
        allow_none=False,
        description='User password.',
        validate=validate.Length(min=1, error='Field cannot be blank.')
    )
    confirm_password = String(
        load_only=True,
        required=True,
        allow_none=False,
        description='User password confirm.',
        validate=validate.Length(min=1, error='Field cannot be blank.')
    )

    @validates_schema(skip_on_field_errors=True)
    def validate_password_confirmation(self, data):
        if data['password'] != data['confirm_password']:
            raise ValidationError(
                'Confirm password must equal to a new password.',
                field_names=['confirm_password', ]
            )

    def load(self, data, many=None, partial=None):
        result = super(CreateUserSchema, self).load(data, many=many, partial=partial)  # NOQA
        if not result.errors:
            result.data.pop('confirm_password')
        return result

    class Meta:
        fields = (
            'id',
            'username',
            'password',
            'confirm_password'
        )


class UserProfileSchema(BaseUserSchema):
    id = String(
        dump_only=True,
        description='Unique document identifier of a User.'
    )
    username = String(
        dump_only=True,
        description='Unique username.'
    )

    class Meta:
        fields = (
            'id',
            'username',
        )
