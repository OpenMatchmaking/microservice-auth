import os
from sanic_script import Command
from app import app


class RunServerCommand(Command):
    """
    Run the HTTP/HTTPS server.
    """
    app = app

    def run(self, *args, **kwargs):
        self.app.run(
            host=kwargs.get('host', os.environ.get("APP_HOST", None)),
            port=kwargs.get('port', os.environ.get("APP_PORT", None)),
            debug=kwargs.get('debug', os.environ.get("APP_DEBUG", False)),
            ssl=kwargs.get('ssl', os.environ.get("APP_SSL", None)),
            workers=kwargs.get('workers', os.environ.get("APP_WORKERS", 1)),
        )
