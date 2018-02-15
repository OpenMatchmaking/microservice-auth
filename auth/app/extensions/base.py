from sanic import Sanic


class BaseExtension(object):
    app_attribute = None

    def __init__(self, app: Sanic=None, app_attribute: str=None, *args, **kwargs):
        self.app = app
        self.app_attribute = app_attribute or self.app_attribute

        if app:
            self.init_app(app, *args, **kwargs)

    def init_app(self, app: Sanic, *args, **kwargs):
        raise NotImplementedError('`init_app()` method must be implemented.')

    def get_from_app_config(self, app, parameter, default=None):
        return getattr(app.config, parameter, default)
