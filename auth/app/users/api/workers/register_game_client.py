import json

from aioamqp import AmqpClosedConnection
from marshmallow import ValidationError
from sanic_amqp_ext import AmqpWorker
from sage_utils.constants import VALIDATION_ERROR
from sage_utils.wrappers import Response


class RegisterGameClientWorker(AmqpWorker):
    QUEUE_NAME = 'auth.users.register'
    REQUEST_EXCHANGE_NAME = 'open-matchmaking.auth.users.register.direct'
    RESPONSE_EXCHANGE_NAME = 'open-matchmaking.responses.direct'
    CONTENT_TYPE = 'application/json'

    DEFAULT_GROUP_NAME = "Game client"

    def __init__(self, app, *args, **kwargs):
        super(RegisterGameClientWorker, self).__init__(app, *args, **kwargs)
        from app.groups.documents import Group
        from app.users.documents import User
        from app.users.api.schemas import CreateUserSchema
        self.user_document = User
        self.group_document = Group
        self.schema = CreateUserSchema

    async def validate_data(self, raw_data):
        try:
            data = json.loads(raw_data.strip())
        except json.decoder.JSONDecodeError:
            data = {}

        deserializer = self.schema()
        result = deserializer.load(data)
        if result.errors:
            raise ValidationError(result.errors)

        return result.data

    async def validate_username_for_uniqueness(self, username):
        users = await self.user_document.collection.count_documents({"username": username})
        if users:
            raise ValidationError(
                "Username must be unique.",
                field_names=["username", ]
            )

    async def register_game_client(self, raw_data):
        try:
            data = await self.validate_data(raw_data)
            await self.validate_username_for_uniqueness(data["username"])
        except ValidationError as exc:
            return Response.from_error(VALIDATION_ERROR, exc.normalized_messages())

        user_groups = await self.group_document.collection \
            .find({"name": self.DEFAULT_GROUP_NAME}) \
            .collation({"locale": "en", "strength": 2}) \
            .to_list(1)
        data['groups'] = [group['_id'] for group in user_groups]
        user = self.user_document(**data)
        await user.commit()
        serializer = self.schema()
        return Response.with_content(serializer.dump(user).data)

    async def process_request(self, channel, body, envelope, properties):
        response = await self.register_game_client(body)
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
