from bson.objectid import ObjectId
from jwt import InvalidTokenError
from sanic.response import json
from marshmallow import ValidationError

from app.generic.views import APIView
from app.generic.utils import wrap_error
from app.token.exceptions import MissingAuthorizationHeader, InvalidHeaderPrefix
from app.token.json_web_token import extract_and_decode_token


class RegisterGameClientView(APIView):
    default_group_name = "Game client"

    def __init__(self):
        super(RegisterGameClientView, self).__init__()
        from app.users.documents import User
        from app.groups.documents import Group
        self.user_document = User
        self.group_document = Group

        from app.users.api.v1.schemas import CreateUserSchema
        self.schema = CreateUserSchema

    async def validate_username_for_uniqueness(self, username):
        users = await self.user_document.find({"username": username}).count()
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
        user = self.user_document(**data)
        await user.commit()
        return json(self.serialize(user), status=201)


class UserProfileView(APIView):

    def __init__(self):
        super(UserProfileView, self).__init__()
        from app.users.documents import User
        from app.groups.documents import Group
        from app.permissions.documents import Permission
        self.user_document = User
        self.group_document = Group
        self.permission_document = Permission

        from app.users.api.v1.schemas import UserProfileSchema
        self.schema = UserProfileSchema

    async def get(self, request):
        try:
            token = extract_and_decode_token(request)
        except (MissingAuthorizationHeader, InvalidHeaderPrefix) as exc:
            return json(exc.details, status=exc.status_code)
        except InvalidTokenError as exc:
            return json(wrap_error(str(exc)), status=400)

        user_id = token.get('user_id', None)
        user = await self.user_document.find_one({"_id": ObjectId(user_id)})
        if not user:
            return json(wrap_error("User was not found."), status=400)

        pipeline = [
            {'$match': {'_id': {'$in': [obj.pk for obj in user.groups]}}},
            {'$group': {'_id': None, 'permission_ids': {'$addToSet': '$permissions'}}},
            {'$project': {
                'permission_ids': {
                    '$reduce': {
                        'input': '$permission_ids',
                        'initialValue': [],
                        'in': {'$setUnion': ['$$value', '$$this']}
                    }
                }
            }}
        ]
        permission_ids = await self.group_document.collection.aggregate(pipeline).to_list(1)
        permission_ids = permission_ids[0]['permission_ids'] if permission_ids else []

        permissions = []
        if permission_ids:
            pipeline = [
                {'$match': {'_id': {'$in': permission_ids}}},
                {'$group': {'_id': None, 'codenames': {'$addToSet': '$codename'}}},
            ]
            permissions = await self.permission_document.collection.aggregate(pipeline).to_list(1)
            permissions = permissions[0]['codenames'] if permissions else []

        serialized_user = self.serialize(user)
        serialized_user['permissions'] = permissions
        return json(serialized_user, status=200)
