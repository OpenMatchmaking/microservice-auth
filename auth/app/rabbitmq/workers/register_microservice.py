import json

from aioamqp import AmqpClosedConnection
from marshmallow import ValidationError
from sanic_amqp_ext import AmqpWorker

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
        from app.microservices.schemas import MicroserviceSchema
        self.microservice_document = Microservice
        self.schema = MicroserviceSchema
        self.group_document = Group

    async def validate_data(self, raw_data):
        try:
            data = json.loads(raw_data.strip())
        except json.decoder.JSONDecodeError:
            data = {}

        deserializer = self.schema()
        result = deserializer.load(data)
        if result.errors:
            raise ValidationError(result.errors)

        await deserializer.load_permissions(result.data['permissions'], result.data)
        return result.data

    async def update_groups(self, old_permissions, new_permissions):
        await self.group_document.synchronize_permissions(old_permissions, new_permissions)

    async def register_microservice(self, raw_data):
        try:
            data = await self.validate_data(raw_data)
        except ValidationError as exc:
            response = wrap_error(exc.normalized_messages())
            response.update({'status': 400})
            return response

        old_microservice = await self.microservice_document.find_one({'name': data['name']})
        old_permissions = [obj.pk for obj in old_microservice.permissions] if old_microservice else []  # NOQA
        new_permissions = data['permissions'][:]

        await self.microservice_document.collection.replace_one(
            {'name': data['name']}, replacement=data, upsert=True
        )

        self.app.loop.create_task(self.update_groups(old_permissions, new_permissions))
        return {CONTENT_FIELD_NAME: "OK", "status": 200}

    async def process_request(self, channel, body, envelope, properties):
        response = await self.register_microservice(body)

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
