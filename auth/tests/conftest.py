import pytest
from pymongo import MongoClient

from app import app as sanic_app


@pytest.yield_fixture(scope="module")
def app_factory():
    GENERIC_MONGODB_URI = 'mongodb://{}:{}@{}:{}'.format(
        sanic_app.config['TEST_MONGODB_USERNAME'],
        sanic_app.config['TEST_MONGODB_PASSWORD'],
        sanic_app.config['TEST_MONGODB_HOST'],
        sanic_app.config['TEST_MONGODB_PORT'],
    )
    client = MongoClient(GENERIC_MONGODB_URI)
    database = client[sanic_app.config["TEST_MONGODB_DATABASE"]]
    database['test_collection'].insert_one({'key': 'value'})

    sanic_app.config.update({
        "MONGODB_USERNAME": sanic_app.config["TEST_MONGODB_USERNAME"],
        "MONGODB_PASSWORD": sanic_app.config["TEST_MONGODB_PASSWORD"],
        "MONGODB_HOST": sanic_app.config["TEST_MONGODB_HOST"],
        "MONGODB_PORT": sanic_app.config["TEST_MONGODB_PORT"],
        "MONGODB_DATABASE": sanic_app.config["TEST_MONGODB_DATABASE"],
        "MONGODB_URI": sanic_app.config["TEST_MONGODB_URI"],
    })
    yield sanic_app

    database.drop_collection('test_collection')
    client.drop_database(database)


@pytest.fixture
def sanic_server(loop, app_factory, test_client):
    return loop.run_until_complete(test_client(app_factory))
