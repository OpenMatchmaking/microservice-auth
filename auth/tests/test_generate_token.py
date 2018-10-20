from sage_utils.amqp.clients import RpcAmqpClient
from sage_utils.constants import NOT_FOUND_ERROR, VALIDATION_ERROR
from sage_utils.wrappers import Response

from app.token.api.workers.generate_token import GenerateTokenWorker
from app.users.documents import User


REQUEST_QUEUE = GenerateTokenWorker.QUEUE_NAME
REQUEST_EXCHANGE = GenerateTokenWorker.REQUEST_EXCHANGE_NAME
RESPONSE_EXCHANGE = GenerateTokenWorker.RESPONSE_EXCHANGE_NAME


async def test_generate_token_returns_a_new_token_pair(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    payload = {
        "username": "user",
        "password": "123456"
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
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in content.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in content.keys()

    await User.collection.delete_many({})


async def test_generate_token_returns_error_for_an_invalid_username(sanic_server):
    await User.collection.delete_many({})
    await User(**{"username": "user", "password": "123456"}).commit()

    payload = {
        "username": "NON_EXISTING_USER",
        "password": "123456"
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

    assert len(error.keys()) == 2
    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == NOT_FOUND_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == "User wasn't found or " \
                                                       "specified an invalid password."

    await User.collection.delete_many({})


async def test_generate_token_returns_error_for_an_invalid_password(sanic_server):
    await User.collection.delete_many({})
    await User(**{"username": "user", "password": "123456"}).commit()

    payload = {
        "username": "user",
        "password": "WRONG_PASSWORD"
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

    assert len(error.keys()) == 2
    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == NOT_FOUND_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == "User wasn't found or " \
                                                       "specified an invalid password."

    await User.collection.delete_many({})


async def test_generate_token_returns_validation_error_for_empty_body(sanic_server):
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
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME].keys()) == 2

    assert 'username' in error[Response.ERROR_DETAILS_FIELD_NAME].keys()
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME]['username']) == 1
    assert error[Response.ERROR_DETAILS_FIELD_NAME]['username'][0] == 'Missing data for ' \
                                                                      'required field.'

    assert 'password' in error[Response.ERROR_DETAILS_FIELD_NAME].keys()
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME]['password']) == 1
    assert error[Response.ERROR_DETAILS_FIELD_NAME]['password'][0] == 'Missing data for ' \
                                                                      'required field.'
