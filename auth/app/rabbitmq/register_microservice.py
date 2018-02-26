import json

from aioamqp import AmqpClosedConnection
from marshmallow import ValidationError

from app.extensions.amqp import AmqpWorker
from app.generic.utils import CONTENT_FIELD_NAME, wrap_error


class RegisterMicroserviceWorker(AmqpWorker):
    QUEUE_NAME = 'auth.microservices.register'
    REQUEST_EXCHANGE_NAME = 'open-matchmaking.direct'
    RESPONSE_EXCHANGE_NAME = 'open-matchmaking.responses.direct'
    CONTENT_TYPE = 'application/json'

    def __init__(self, app, *args, **kwargs):
        super(RegisterMicroserviceWorker, self).__init__(app, *args, **kwargs)
        from app.microservices.documents import Microservice
        from app.groups.documents import Group
        from app.permissions.documents import Permission
        from app.microservices.schemas import MicroserviceSchema

        self.microservice_document = Microservice
        self.schema = MicroserviceSchema
        self.group_document = Group
        self.permission_document = Permission

    def validate_data(self, raw_data):
        try:
            data = json.loads(raw_data.strip())
        except json.decoder.JSONDecodeError:
            data = {}

        result = self.schema().load(data)
        if result.errors:
            raise ValidationError(result.errors)

        return result.data

    async def register_microservice(self, raw_data):
        try:
            data = self.validate_data(raw_data)
        except ValidationError as exc:
            response = wrap_error(exc.normalized_messages())
            response.update({'status': 400})
            return response

        # await self.microservice_document.create_or_update(data)
        return {CONTENT_FIELD_NAME: "OK", "status": 200}

    async def process_request(self, channel, body, envelope, properties):
        response = await self.register_microservice(body)
        print(response)

        if properties.reply_to:
            await channel.publish(
                json.dumps(response),
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
        event_loop = self.app.loop
        event_loop.create_task(self.process_request(channel, body, envelope, properties))

    async def run(self, *args, **kwargs):
        try:
            _transport, protocol = await self.app.amqp.connect()
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
