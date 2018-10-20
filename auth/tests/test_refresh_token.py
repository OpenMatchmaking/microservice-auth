from asyncio import sleep as asyncio_sleep

from sage_utils.amqp.clients import RpcAmqpClient
from sage_utils.constants import NOT_FOUND_ERROR, TOKEN_ERROR, VALIDATION_ERROR
from sage_utils.wrappers import Response

from app.token.api.workers.generate_token import GenerateTokenWorker
from app.token.api.workers.refresh_token import RefreshTokenWorker
from app.users.documents import User


REQUEST_TOKEN_QUEUE = GenerateTokenWorker.QUEUE_NAME
REQUEST_TOKEN_EXCHANGE = GenerateTokenWorker.REQUEST_EXCHANGE_NAME
RESPONSE_TOKEN_EXCHANGE = GenerateTokenWorker.RESPONSE_EXCHANGE_NAME

REQUEST_QUEUE = RefreshTokenWorker.QUEUE_NAME
REQUEST_EXCHANGE = RefreshTokenWorker.REQUEST_EXCHANGE_NAME
RESPONSE_EXCHANGE = RefreshTokenWorker.RESPONSE_EXCHANGE_NAME


async def test_refresh_token_returns_new_access_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    payload = {
        "username": "user",
        "password": "123456"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_TOKEN_QUEUE,
        request_exchange=REQUEST_TOKEN_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_TOKEN_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    tokens = response[Response.CONTENT_FIELD_NAME]

    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    refresh_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token'],
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: tokens['refresh_token'],
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=refresh_payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    content = response[Response.CONTENT_FIELD_NAME]

    assert 'access_token' in content.keys()
    assert 'refresh_token' not in content.keys()

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_returns_error_for_not_existing_user(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    payload = {
        "username": "user",
        "password": "123456"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_TOKEN_QUEUE,
        request_exchange=REQUEST_TOKEN_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_TOKEN_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    tokens = response[Response.CONTENT_FIELD_NAME]

    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    await User.collection.delete_many({})
    await asyncio_sleep(0.1)

    refresh_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token'],
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: tokens['refresh_token'],
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=refresh_payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()
    errors = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_TYPE_FIELD_NAME] == NOT_FOUND_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_DETAILS_FIELD_NAME] == "User wasn't found."

    await User.collection.delete_many({'id': user.id})


async def test_refresh_token_returns_error_for_an_invalid_access_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    payload = {
        "username": "user",
        "password": "123456"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_TOKEN_QUEUE,
        request_exchange=REQUEST_TOKEN_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_TOKEN_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    tokens = response[Response.CONTENT_FIELD_NAME]

    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    refresh_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token'][:-1],
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: tokens['refresh_token'],
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=refresh_payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()
    errors = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_TYPE_FIELD_NAME] == TOKEN_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_DETAILS_FIELD_NAME] == 'Signature verification failed.'

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_returns_an_error_for_a_missing_tokens(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    payload = {
        "username": "user",
        "password": "123456"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_TOKEN_QUEUE,
        request_exchange=REQUEST_TOKEN_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_TOKEN_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    tokens = response[Response.CONTENT_FIELD_NAME]

    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload={})

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()
    errors = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_TYPE_FIELD_NAME] == VALIDATION_ERROR

    assert len(errors[Response.ERROR_DETAILS_FIELD_NAME]) == 2

    assert 'access_token' in errors[Response.ERROR_DETAILS_FIELD_NAME].keys()
    assert len(errors[Response.ERROR_DETAILS_FIELD_NAME]['access_token']) == 1
    assert errors[Response.ERROR_DETAILS_FIELD_NAME]['access_token'][0] == 'Missing data for ' \
                                                                           'required field.'

    assert 'refresh_token' in errors[Response.ERROR_DETAILS_FIELD_NAME].keys()
    assert len(errors[Response.ERROR_DETAILS_FIELD_NAME]['refresh_token']) == 1
    assert errors[Response.ERROR_DETAILS_FIELD_NAME]['refresh_token'][0] == 'Missing data for ' \
                                                                            'required field.'

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_returns_an_error_for_an_refresh_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    payload = {
        "username": "user",
        "password": "123456"
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_TOKEN_QUEUE,
        request_exchange=REQUEST_TOKEN_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_TOKEN_EXCHANGE
    )
    response = await client.send(payload=payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    tokens = response[Response.CONTENT_FIELD_NAME]

    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    refresh_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token'],
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: "INVALID_REFRESH_TOKEN",
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=refresh_payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()
    errors = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_TYPE_FIELD_NAME] == TOKEN_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_DETAILS_FIELD_NAME] == "Specified an invalid `refresh_token`."

    await User.collection.delete_one({'id': user.id})
