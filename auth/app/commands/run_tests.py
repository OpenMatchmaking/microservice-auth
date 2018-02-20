import os

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

    def setup_environ_for_pytest_cov(self):
        # See: https://github.com/pytest-dev/pytest-cov/issues/117
        os.environ.setdefault('COV_CORE_SOURCE', 'app')
        os.environ.setdefault('COV_CORE_CONFIG', '.coveragerc')
        os.environ.setdefault('COV_CORE_DATAFILE', '.coverage.eager')

    def run(self, *args, **kwargs):
        app = kwargs.get('application')
        self.setup_environ_for_pytest_cov()
        pytest.main(args=["-q", "-v", "--cov", app, "--cov-report",
                          "term-missing", "--tb=native"])
