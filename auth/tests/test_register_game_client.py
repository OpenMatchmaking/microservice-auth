from sage_utils.amqp.clients import RpcAmqpClient
from sage_utils.constants import VALIDATION_ERROR
from sage_utils.wrappers import Response

from app.users.api.workers.register_game_client import RegisterGameClientWorker
from app.users.documents import User


REQUEST_QUEUE = RegisterGameClientWorker.QUEUE_NAME
REQUEST_EXCHANGE = RegisterGameClientWorker.REQUEST_EXCHANGE_NAME
RESPONSE_EXCHANGE = RegisterGameClientWorker.RESPONSE_EXCHANGE_NAME


async def test_users_post_successfully_creates_a_new_user(sanic_server):
    await User.collection.delete_many({})

    payload = {
        "username": "new_user",
        "password": "123456",
        "confirm_password": "123456"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    content = response[Response.CONTENT_FIELD_NAME]

    assert len(content.keys()) == 2

    assert "id" in content

    assert "username" in content
    assert content["username"] == payload["username"]

    await User.collection.delete_many({})


async def test_users_post_returns_validation_error_for_non_unique_username(sanic_server):
    await User.collection.delete_many({})
    await User(**{"username": "new_user", "password": "123456"}).commit()

    payload = {
        "username": "new_user",
        "password": "123456",
        "confirm_password": "123456"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.EVENT_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == VALIDATION_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME].keys()) == 1

    assert 'username' in error[Response.ERROR_DETAILS_FIELD_NAME]
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME]['username']) == 1
    assert error[Response.ERROR_DETAILS_FIELD_NAME]['username'][0] == 'Username must be unique.'

    await User.collection.delete_many({})


async def test_users_post_returns_validation_error_for_not_matched_password(sanic_server):
    payload = {
        "username": "new_user",
        "password": "123456",
        "confirm_password": "ANOTHER_PASSWORD"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.EVENT_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == VALIDATION_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME].keys()) == 1

    details = error[Response.ERROR_DETAILS_FIELD_NAME]
    assert 'confirm_password' in details.keys()
    assert len(details['confirm_password']) == 1
    assert details['confirm_password'][0] == 'Confirm password must equal to a new password.'


async def test_users_post_returns_validation_error_for_missing_fields(sanic_server):
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload={})

    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.EVENT_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == VALIDATION_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME].keys()) == 3

    details = error[Response.ERROR_DETAILS_FIELD_NAME]
    assert 'username' in details.keys()
    assert len(details['username']) == 1
    assert details['username'][0] == 'Missing data for required field.'

    assert 'password' in details.keys()
    assert len(details['password']) == 1
    assert details['password'][0] == 'Missing data for required field.'

    assert 'confirm_password' in details.keys()
    assert len(details['confirm_password']) == 1
    assert details['confirm_password'][0] == 'Missing data for required field.'
