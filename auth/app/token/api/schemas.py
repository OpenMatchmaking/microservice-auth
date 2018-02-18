from marshmallow import Schema, validate
from marshmallow.fields import String


class LoginSchema(Schema):

    username = String(
        required=True,
        load_only=True,
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

    class Meta:
        fields = (
            'username',
            'password'
        )


class RefreshTokenSchema(Schema):

    refresh_token = String(
        load_only=True,
        required=True,
        allow_none=False,
        description='Refresh token',
        validate=validate.Length(min=1, error='Field cannot be blank.')
    )

    class Meta:
        fields = (
            'refresh_token',
        )
