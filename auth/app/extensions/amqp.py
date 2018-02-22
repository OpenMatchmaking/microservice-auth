from aioamqp import connect as amqp_connect
from sanic import Sanic

from app.extensions.base import BaseExtension


class AmqpExtension(BaseExtension):
    app_attribute = 'rabbitmq'
    tasks = []

    def register_task(self, task):
        self.tasks.append(task)

    def get_config(self, app):
        return {
            "login": self.get_from_app_config(app, "AMQP_USERNAME", "guest"),
            "password": self.get_from_app_config(app, "AMQP_PASSWORD", "guest"),
            "host": self.get_from_app_config(app, "AMQP_HOST", "localhost"),
            "port": self.get_from_app_config(app, "AMQP_PORT", 5672),
            "virtualhost": self.get_from_app_config(app, "AMQP_VIRTUAL_HOST", "vhost"),
            "ssl": self.get_from_app_config(app, "AMQP_USING_SSL", False),
        }

    async def connect(self, app, loop):
        config = self.get_config(app)
        config.update({"loop": loop})
        transport, protocol = await amqp_connect(**config)
        return transport, protocol

    def init_app(self, app: Sanic, *args, **kwargs):

        @app.listener('before_server_start')
        async def aioamqp_configure(app_inner, loop):
            def connection_wrapper():
                return self.connect(app_inner, loop)

            client = connection_wrapper
            setattr(app_inner, self.app_attribute, client)

            for task in self.tasks:
                loop.create_task(task(app))

        @app.listener('after_server_stop')
        async def aioamqp_free_resources(app_inner, _loop):
            setattr(app_inner, self.app_attribute, None)
