from sanic_script import Command, Option

from app import app


class RunServerCommand(Command):
    """
    Run the HTTP/HTTPS server.
    """
    app = app

    option_list = (
        Option('--host', '-h', dest='host', default='127.0.0.1'),
        Option('--port', '-p', dest='port', default=8000),
    )

    def run(self, *args, **kwargs):
        self.app.run(
            host=kwargs.get('host', self.app.config["APP_HOST"]),
            port=kwargs.get('port', self.app.config["APP_PORT"]),
            debug=self.app.config["APP_DEBUG"],
            ssl=self.app.config["APP_SSL"],
            workers=self.app.config["APP_WORKERS"],
        )
