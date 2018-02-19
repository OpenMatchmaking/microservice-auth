import pytest
from sanic_script import Command, Option

from app import app


class RunTestsCommand(Command):
    """
    Run py.test for testing Sanic app.
    """
    app = app

    option_list = (
        Option('--app-name', '-a', dest='application', default='app'),
    )

    def run(self, *args, **kwargs):
        app = kwargs.get('application')
        pytest.main(args=["-q", "-v","--cov", app, "--cov-report",
                          "term-missing", "--tb=native"])
