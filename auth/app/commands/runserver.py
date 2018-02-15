from sanic_script import Command, Option

from app import app


class RunServerCommand(Command):
    """
    Run the HTTP/HTTPS server.
    """
    app = app

    option_list = (
        Option('--host', '-h', dest='host', default='0.0.0.0'),
        Option('--port', '-p', dest='port', default=8000),
        Option('--debug', '-d', dest='debug', default=False),
        Option('--ssl', '-s', dest='ssl', default=None),
        Option('--workers', '-w', dest='workers', default=1),
    )

    def run(self, *args, **kwargs):
        self.app.run(
            host=kwargs.get('host', self.app.config["APP_HOST"]),
            port=kwargs.get('port', self.app.config["APP_PORT"]),
            debug=kwargs.get('debug', self.app.config["APP_DEBUG"]),
            ssl=kwargs.get('ssl', self.app.config["APP_SSL"]),
            workers=kwargs.get('workers', self.app.config["APP_WORKERS"]),
        )
