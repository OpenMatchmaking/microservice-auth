import asyncio

from sage_utils.amqp.clients import RpcAmqpClient
from sage_utils.constants import TOKEN_ERROR, NOT_FOUND_ERROR
from sage_utils.wrappers import Response

from app.groups.documents import Group
from app.microservices.documents import Microservice
from app.permissions.documents import Permission
from app.rabbitmq.workers import RegisterMicroserviceWorker
from app.token.api.workers.generate_token import GenerateTokenWorker
from app.users.documents import User
from app.users.api.workers.user_profile import UserProfileWorker

from amqp_client import AmqpTestClient


REQUEST_TOKEN_QUEUE = GenerateTokenWorker.QUEUE_NAME
REQUEST_TOKEN_EXCHANGE = GenerateTokenWorker.REQUEST_EXCHANGE_NAME
RESPONSE_TOKEN_EXCHANGE = GenerateTokenWorker.RESPONSE_EXCHANGE_NAME

REQUEST_REGISTER_MICROSERVICE_QUEUE = RegisterMicroserviceWorker.QUEUE_NAME
REQUEST_REGISTER_MICROSERVICE_EXCHANGE = RegisterMicroserviceWorker.REQUEST_EXCHANGE_NAME
RESPONSE_REGISTER_MICROSERVICE_EXCHANGE = RegisterMicroserviceWorker.RESPONSE_EXCHANGE_NAME

REQUEST_QUEUE = UserProfileWorker.QUEUE_NAME
REQUEST_EXCHANGE = UserProfileWorker.REQUEST_EXCHANGE_NAME
RESPONSE_EXCHANGE = UserProfileWorker.RESPONSE_EXCHANGE_NAME


async def test_user_profile_returns_an_information_about_the_user(sanic_server):
    await Group.collection.delete_many({})
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})
    await User.collection.delete_many({})
    group_config = sanic_server.app.config['DEFAULT_GROUPS']['Game client']
    data = {'name': 'Game client'}
    data.update(group_config.get('init', {}))
    group = Group(**data)
    await group.commit()
    user = User(**{"username": "user", "password": "123456", "groups": [group.id]})
    await user.commit()

    # Register new microservice
    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': [
            {'codename': 'auth.resource.retrieve', 'description': 'get data'},
            {'codename': 'auth.resource.update', 'description': 'update data'},
        ]
    }
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_REGISTER_MICROSERVICE_QUEUE,
        request_exchange=REQUEST_REGISTER_MICROSERVICE_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_REGISTER_MICROSERVICE_EXCHANGE
    )
    response = await client.send(payload=create_data)
    await asyncio.sleep(1.0)
    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    # Get a new token for the user
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

    # And get the user profile with permissions
    user_profile_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token']
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=user_profile_payload)
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    content = response[Response.CONTENT_FIELD_NAME]

    assert len(content.keys()) == 3

    assert 'id' in content.keys()
    assert content['id'] == str(user.id)

    assert 'username' in content.keys()
    assert content['username'] == user.username

    assert 'permissions' in content.keys()
    assert set(content['permissions']) == {'auth.resource.retrieve', 'auth.resource.update'}

    await Group.collection.delete_many({})
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})


async def test_user_profile_returns_an_information_about_the_user_after_microservice_update(sanic_server):  # NOQA
    await Group.collection.delete_many({})
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})
    await User.collection.delete_many({})
    group_config = sanic_server.app.config['DEFAULT_GROUPS']['Game client']
    data = {'name': 'Game client'}
    data.update(group_config.get('init', {}))
    group = Group(**data)
    await group.commit()
    user = User(**{"username": "user", "password": "123456", "groups": [group.id]})
    await user.commit()

    # Register new microservice
    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': [
            {'codename': 'auth.resource.retrieve', 'description': 'get data'},
            {'codename': 'auth.resource.update', 'description': 'update data'},
        ]
    }
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_REGISTER_MICROSERVICE_QUEUE,
        request_exchange=REQUEST_REGISTER_MICROSERVICE_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_REGISTER_MICROSERVICE_EXCHANGE
    )
    response = await client.send(payload=create_data)
    await asyncio.sleep(1.0)
    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    # Get a new token for the user
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

    # And get the user profile with permissions
    user_profile_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token']
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=user_profile_payload)
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    content = response[Response.CONTENT_FIELD_NAME]

    assert len(content.keys()) == 3

    assert 'id' in content.keys()
    assert content['id'] == str(user.id)

    assert 'username' in content.keys()
    assert content['username'] == user.username

    assert 'permissions' in content.keys()
    assert set(content['permissions']) == {'auth.resource.retrieve', 'auth.resource.update'}

    # Update the existing microservice
    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': [
            {'codename': 'auth.resource.retrieve', 'description': 'get data'},
        ]
    }
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_REGISTER_MICROSERVICE_QUEUE,
        request_exchange=REQUEST_REGISTER_MICROSERVICE_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_REGISTER_MICROSERVICE_EXCHANGE
    )
    response = await client.send(payload=create_data)
    await asyncio.sleep(1.0)
    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    # And check the updates
    user_profile_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token']
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=user_profile_payload)
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME in response.keys()
    content = response[Response.CONTENT_FIELD_NAME]

    assert len(content.keys()) == 3

    assert 'id' in content.keys()
    assert content['id'] == str(user.id)

    assert 'username' in content.keys()
    assert content['username'] == user.username

    assert 'permissions' in content.keys()
    assert set(content['permissions']) == {'auth.resource.retrieve', }

    await Group.collection.delete_many({})
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})


async def test_user_profile_returns_validation_error_for_invalid_token(sanic_server):
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

    user_profile_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token'][:-1]
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=user_profile_payload)
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == TOKEN_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'Signature verification failed.'

    await User.collection.delete_many({})


async def test_user_profile_returns_user_was_not_found_error(sanic_server):
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
    await asyncio.sleep(0.1)

    user_profile_payload = {
        sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME']: tokens['access_token']
    }
    client = RpcAmqpClient(
        sanic_server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=user_profile_payload)
    assert Response.EVENT_FIELD_NAME in response.keys()
    assert Response.ERROR_FIELD_NAME in response.keys()
    assert Response.CONTENT_FIELD_NAME not in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == NOT_FOUND_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'User was not found.'

    await User.collection.delete_many({})
