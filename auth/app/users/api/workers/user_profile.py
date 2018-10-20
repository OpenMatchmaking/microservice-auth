import json

from aioamqp import AmqpClosedConnection
from bson.objectid import ObjectId
from jwt import InvalidTokenError
from marshmallow import ValidationError
from sanic_amqp_ext import AmqpWorker
from sage_utils.constants import VALIDATION_ERROR, NOT_FOUND_ERROR, TOKEN_ERROR
from sage_utils.wrappers import Response

from app.token.json_web_token import extract_and_decode_token


class UserProfileWorker(AmqpWorker):
    QUEUE_NAME = 'auth.users.retrieve'
    REQUEST_EXCHANGE_NAME = 'open-matchmaking.auth.users.retrieve.direct'
    RESPONSE_EXCHANGE_NAME = 'open-matchmaking.responses.direct'
    CONTENT_TYPE = 'application/json'

    DEFAULT_GROUP_NAME = "Game client"

    def __init__(self, app, *args, **kwargs):
        super(UserProfileWorker, self).__init__(app, *args, **kwargs)
        from app.users.documents import User
        from app.groups.documents import Group
        from app.permissions.documents import Permission
        from app.users.api.schemas import UserProfileSchema, UserTokenSchema
        self.user_document = User
        self.group_document = Group
        self.permission_document = Permission
        self.schema = UserProfileSchema
        self.token_schema = UserTokenSchema

    def validate_data(self, raw_data):
        try:
            data = json.loads(raw_data.strip())
        except json.decoder.JSONDecodeError:
            data = {}

        deserializer = self.token_schema()
        result = deserializer.load(data)
        if result.errors:
            raise ValidationError(result.errors)

        return extract_and_decode_token(self.app, result.data)

    async def collect_user_permissions(self, user):
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

        return permissions

    async def get_user_profile(self, raw_data):
        try:
            token = self.validate_data(raw_data)
        except ValidationError as exc:
            return Response.from_error(VALIDATION_ERROR, exc.normalized_messages())
        except InvalidTokenError as exc:
            return Response.from_error(TOKEN_ERROR, str(exc))

        user_id = token.get('user_id', None)
        user = await self.user_document.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response.from_error(NOT_FOUND_ERROR, "User was not found.")

        serializer = self.schema()
        serialized_user = serializer.dump(user).data
        serialized_user['permissions'] = await self.collect_user_permissions(user)
        return Response.with_content(serialized_user)

    async def process_request(self, channel, body, envelope, properties):
        response = await self.get_user_profile(body)
        response.data[Response.EVENT_FIELD_NAME] = properties.correlation_id

        if properties.reply_to:
            await channel.publish(
                json.dumps(response.data),
                exchange_name=self.RESPONSE_EXCHANGE_NAME,
                routing_key=properties.reply_to,
                properties={
                    'content_type': self.CONTENT_TYPE,
                    'delivery_mode': 2,
                    'correlation_id': properties.correlation_id
                },
                mandatory=True
            )

        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    async def consume_callback(self, channel, body, envelope, properties):
        self.app.loop.create_task(self.process_request(channel, body, envelope, properties))

    async def run(self, *args, **kwargs):
        try:
            _transport, protocol = await self.connect()
        except AmqpClosedConnection as exc:
            print(exc)
            return

        channel = await protocol.channel()
        await channel.queue_declare(
            queue_name=self.QUEUE_NAME,
            durable=True,
            passive=False,
            auto_delete=False
        )
        await channel.queue_bind(
            queue_name=self.QUEUE_NAME,
            exchange_name=self.REQUEST_EXCHANGE_NAME,
            routing_key=self.QUEUE_NAME
        )
        await channel.basic_qos(prefetch_count=1, prefetch_size=0, connection_global=False)
        await channel.basic_consume(self.consume_callback, queue_name=self.QUEUE_NAME)
