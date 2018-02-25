import json

from aioamqp import AmqpClosedConnection

from app.extensions.amqp import AmqpWorker


class RegisterMicroserviceWorker(AmqpWorker):
    QUEUE_NAME = 'auth.microservices.register'
    REQUEST_EXCHANGE_NAME = 'open-matchmaking.direct'
    RESPONSE_EXCHANGE_NAME = 'open-matchmaking.responses.direct'
    CONTENT_TYPE = 'application/json'

    def validate_data(self, data):
        return json.loads(data)

    # TODO: Implement validating JSON data and fill the MongoDB if it's valid
    async def process_request(self, channel, body, envelope, properties):
        response = self.validate_data(body)

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
