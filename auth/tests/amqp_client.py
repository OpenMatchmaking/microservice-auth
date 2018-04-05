import asyncio
import json
from copy import deepcopy


class AmqpTestClient(object):
    CONTENT_TYPE = 'application/json'
    DEFAULT_PROPERTIES = {
        'content_type': CONTENT_TYPE,
        'delivery_mode': 2,
        'correlation_id': 'test-event-name'
    }

    def __init__(self, app, routing_key, request_exchange='',
                 response_queue=None, response_exchange=''):
        self.app = app
        self.routing_key = routing_key
        self.request_exchange = request_exchange
        self.response_queue = response_queue
        self.response_exchange = response_exchange
        self.transport = None
        self.protocol = None
        self.channel = None

        self.waiter = asyncio.Event()
        self._response_queue_name = None
        self._response = None

    @property
    def response_queue_name(self):
        return self._response_queue_name

    async def connect(self):
        self.transport, self.protocol = await self.app.amqp.connect()
        self.channel = await self.protocol.channel()

        if self.response_queue is not None:
            result = await self.channel.queue_declare(
                queue_name=self.response_queue,
                exclusive=True,
                durable=True,
                passive=False,
                auto_delete=True,
            )
            self._response_queue_name = result['queue']
            await self.channel.queue_bind(
                queue_name=self.response_queue_name,
                exchange_name=self.response_exchange,
                routing_key=self.response_queue_name
            )
            await self.channel.basic_qos(
                prefetch_count=1,
                prefetch_size=0,
                connection_global=False
            )
            await self.channel.basic_consume(
                self.on_response,
                queue_name=self._response_queue_name,
            )

    async def on_response(self, _channel, body, _envelope, _properties):
        self._response = json.loads(body)
        self.waiter.set()

    async def send(self, payload={}, properties={}, raw_data=False):
        if not self.protocol:
            await self.connect()

        request_properties = deepcopy(self.DEFAULT_PROPERTIES)
        request_properties.update({'reply_to': self.response_queue_name})
        request_properties.update(properties)
        await self.channel.publish(
            payload if raw_data else json.dumps(payload),
            exchange_name=self.request_exchange,
            routing_key=self.routing_key,
            properties=request_properties
        )

        response = None
        if self.response_queue_name is not None:
            await self.waiter.wait()
            response = self._response

        await self.protocol.close()
        self.protocol = None
        self.transport = None
        return response
