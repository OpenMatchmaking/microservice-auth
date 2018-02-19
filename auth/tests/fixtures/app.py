import pytest
from app import app


@pytest.fixture(scope="class", autouse=True)
def test_app():
    app.config['MONGODB_DATABASE'] = 'test_database'
    yield app
