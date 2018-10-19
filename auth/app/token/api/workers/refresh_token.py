import json

from aioamqp import AmqpClosedConnection
from bson.objectid import ObjectId
from jwt.exceptions import InvalidTokenError, InvalidSignatureError
from marshmallow import ValidationError
from sage_utils.constants import VALIDATION_ERROR, NOT_FOUND_ERROR, TOKEN_ERROR
from sage_utils.wrappers import Response
from sanic_amqp_ext import AmqpWorker

from app.token.json_web_token import build_payload, extract_and_decode_token, \
    get_redis_key_by_user, generate_access_token
from app.token.redis import get_refresh_token_from_redis


class RefreshTokenWorker(AmqpWorker):
    QUEUE_NAME = 'auth.token.refresh'
    REQUEST_EXCHANGE_NAME = 'open-matchmaking.auth.token.refresh.direct'
    RESPONSE_EXCHANGE_NAME = 'open-matchmaking.responses.direct'
    CONTENT_TYPE = 'application/json'

    def __init__(self, app, *args, **kwargs):
        super(RefreshTokenWorker, self).__init__(app, *args, **kwargs)
        from app.token.api.schemas import RefreshTokenSchema
        from app.users.documents import User
        self.user_document = User
        self.schema = RefreshTokenSchema

    def validate_data(self, raw_data):
        try:
            data = json.loads(raw_data.strip())
        except json.decoder.JSONDecodeError:
            data = {}

        deserializer = self.schema()
        result = deserializer.load(data)
        if result.errors:
            raise ValidationError(result.errors)

        return result.data

    async def get_user_by_id(self, user_id):
        if not user_id:
            return None

        user = await self.user_document.find_one({"_id": ObjectId(user_id)})
        return user

    async def refresh_token(self, raw_data):
        try:
            data = self.validate_data(raw_data)
            access_token = extract_and_decode_token(self.app, data)
        except ValidationError as exc:
            return Response.from_error(VALIDATION_ERROR, exc.normalized_messages())
        except (InvalidTokenError, InvalidSignatureError) as exc:
            return Response.from_error(TOKEN_ERROR, str(exc))

        user_id = access_token.get('user_id', None)
        user = await self.get_user_by_id(user_id)
        if not user:
            return Response.from_error(NOT_FOUND_ERROR, "User wasn't found.")

        refresh_token = data['refresh_token'].strip()
        key = get_redis_key_by_user(self.app, user.username)
        existing_refresh_token = await get_refresh_token_from_redis(self.app.redis, key)

        if existing_refresh_token != refresh_token:
            return Response.from_error(TOKEN_ERROR, "Specified an invalid `refresh_token`.")

        secret = self.app.config["JWT_SECRET_KEY"]
        algorithm = self.app.config["JWT_ALGORITHM"]
        payload = build_payload(self.app, extra_data={"user_id": str(user.pk)})
        new_access_token = generate_access_token(payload, secret, algorithm)
        response = {self.app.config["JWT_ACCESS_TOKEN_FIELD_NAME"]: new_access_token}
        return Response.with_content(response)

    async def process_request(self, channel, body, envelope, properties):
        response = await self.refresh_token(body)
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
