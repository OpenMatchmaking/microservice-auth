from freezegun import freeze_time
from sage_utils.amqp.clients import RpcAmqpClient
from sage_utils.constants import VALIDATION_ERROR, TOKEN_ERROR
from sage_utils.wrappers import Response

from app.token.api.workers.generate_token import GenerateTokenWorker
from app.token.api.workers.verify_token import VerifyTokenWorker
from app.users.documents import User


REQUEST_TOKEN_QUEUE = GenerateTokenWorker.QUEUE_NAME
REQUEST_TOKEN_EXCHANGE = GenerateTokenWorker.REQUEST_EXCHANGE_NAME
RESPONSE_TOKEN_EXCHANGE = GenerateTokenWorker.RESPONSE_EXCHANGE_NAME

REQUEST_QUEUE = VerifyTokenWorker.QUEUE_NAME
REQUEST_EXCHANGE = VerifyTokenWorker.REQUEST_EXCHANGE_NAME
RESPONSE_EXCHANGE = VerifyTokenWorker.RESPONSE_EXCHANGE_NAME


async def test_verify_token_returns_is_valid_for_correct_access_token(sanic_server):
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

    verify_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token']
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=verify_payload)

    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    content = response[Response.CONTENT_FIELD_NAME]

    assert 'is_valid' in content.keys()
    assert content['is_valid'] is True

    await User.collection.delete_one({'id': user.id})


async def test_verify_token_return_a_validation_error_for_a_missing_access_token(sanic_server):
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
    assert Response.CONTENT_FIELD_NAME not in response.keys()

    errors = response[Response.ERROR_FIELD_NAME]
    assert len(errors.keys()) == 2
    assert 'is_valid' not in errors.keys()

    assert Response.ERROR_TYPE_FIELD_NAME in errors.keys()
    assert errors[Response.ERROR_TYPE_FIELD_NAME] == VALIDATION_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in errors.keys()

    access_token_field = sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']
    assert access_token_field in errors[Response.ERROR_DETAILS_FIELD_NAME]
    assert len(errors[Response.ERROR_DETAILS_FIELD_NAME][access_token_field]) == 1
    assert errors[Response.ERROR_DETAILS_FIELD_NAME][access_token_field][0] == 'Missing data for ' \
                                                                               'required field.'


async def test_verify_token_return_error_for_expired_access_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    payload = {
        "username": "user",
        "password": "123456"
    }
    with freeze_time("2000-01-01"):
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

    verify_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token']
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=verify_payload)

    assert len(response.keys()) == 2
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == TOKEN_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'Signature has expired.'

    await User.collection.delete_one({'id': user.id})


async def test_verify_token_return_error_for_invalid_access_token(sanic_server):
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

    verify_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token'][:-1]
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=verify_payload)

    assert len(response.keys()) == 2
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()

    error = response[Response.ERROR_FIELD_NAME]
    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == TOKEN_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'Signature verification failed.'

    await User.collection.delete_one({'id': user.id})
