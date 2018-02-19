from sanic.response import json
from marshmallow import ValidationError

from app.generic.views import APIView
from app.generic.utils import wrap_error


class RegisterGameClientView(APIView):
    default_group_name = "Game client"

    def __init__(self):
        super(RegisterGameClientView, self).__init__()
        from app.users.documents import User
        from app.users.documents import Group
        self.document = User
        self.group_document = Group

        from app.users.api.v1.schemas import CreateUserSchema
        self.schema = CreateUserSchema

    async def validate_username_for_uniqueness(self, username):
        users = await self.document.find({"username": username}).count()
        if users:
            raise ValidationError(
                "Username must be unique.",
                field_names=["username", ]
            )

    async def post(self, request):
        try:
            data = self.deserialize(request.json)
            await self.validate_username_for_uniqueness(data["username"])
        except ValidationError as exc:
            errors = exc.normalized_messages()
            return json(wrap_error(errors), status=400)

        data['groups'] = await self.group_document\
            .find({"name": self.default_group_name})\
            .collation({"locale": "en", "strength": 2})\
            .to_list(1)
        user = self.document(**data)
        await user.commit()
        return json(self.serialize(user), status=201)
