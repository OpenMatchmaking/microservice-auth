import json

from aioamqp import AmqpClosedConnection
from marshmallow import ValidationError
from sanic_amqp_ext import AmqpWorker
from sage_utils.constants import VALIDATION_ERROR, NOT_FOUND_ERROR
from sage_utils.wrappers import Response


from app.token.json_web_token import build_payload, generate_token_pair


class GenerateTokenWorker(AmqpWorker):
    QUEUE_NAME = 'auth.token.new'
    REQUEST_EXCHANGE_NAME = 'open-matchmaking.auth.token.new.direct'
    RESPONSE_EXCHANGE_NAME = 'open-matchmaking.responses.direct'
    CONTENT_TYPE = 'application/json'

    def __init__(self, app, *args, **kwargs):
        super(GenerateTokenWorker, self).__init__(app, *args, **kwargs)
        from app.users.documents import User
        from app.token.api.schemas import LoginSchema
        self.user_document = User
        self.schema = LoginSchema

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

    async def generate_token(self, raw_data):
        try:
            data = self.validate_data(raw_data)
        except ValidationError as exc:
            return Response.from_error(VALIDATION_ERROR, exc.normalized_messages())

        user = await self.user_document.find_one({"username": data["username"]})
        if not user or (user and not user.verify_password(data["password"])):
            return Response.from_error(
                NOT_FOUND_ERROR, "User wasn't found or specified an invalid password."
            )

        payload = build_payload(self.app, extra_data={"user_id": str(user.pk)})
        response = await generate_token_pair(self.app, payload, user.username)
        return Response.with_content(response)

    async def process_request(self, channel, body, envelope, properties):
        response = await self.generate_token(body)
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
        await channel.basic_qos(prefetch_count=50, prefetch_size=0, connection_global=False)
        await channel.basic_consume(self.consume_callback, queue_name=self.QUEUE_NAME)
