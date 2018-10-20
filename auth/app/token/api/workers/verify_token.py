import json

from aioamqp import AmqpClosedConnection
from jwt.exceptions import InvalidTokenError, InvalidSignatureError
from marshmallow import ValidationError
from sanic_amqp_ext import AmqpWorker
from sage_utils.constants import VALIDATION_ERROR, TOKEN_ERROR
from sage_utils.wrappers import Response


from app.token.json_web_token import extract_and_decode_token


class VerifyTokenWorker(AmqpWorker):
    QUEUE_NAME = 'auth.token.verify'
    REQUEST_EXCHANGE_NAME = 'open-matchmaking.auth.token.verify.direct'
    RESPONSE_EXCHANGE_NAME = 'open-matchmaking.responses.direct'
    CONTENT_TYPE = 'application/json'

    def __init__(self, app, *args, **kwargs):
        super(VerifyTokenWorker, self).__init__(app, *args, **kwargs)
        from app.token.api.schemas import VerifyTokenSchema
        self.schema = VerifyTokenSchema

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

    def verify_token(self, raw_data):
        try:
            data = self.validate_data(raw_data)
            extract_and_decode_token(self.app, data)
        except ValidationError as exc:
            return Response.from_error(VALIDATION_ERROR, exc.normalized_messages())
        except (InvalidTokenError, InvalidSignatureError) as exc:
            return Response.from_error(TOKEN_ERROR, str(exc))

        return Response.with_content({"is_valid": True})

    async def process_request(self, channel, body, envelope, properties):
        response = self.verify_token(body)
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
