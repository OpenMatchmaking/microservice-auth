import asyncio
import json

from app.generic.utils import CONTENT_FIELD_NAME, EVENT_FIELD_NAME, ERROR_FIELD_NAME, \
    AUTHORIZATION_ERROR, TOKEN_ERROR, NOT_FOUND_ERROR, HEADER_ERROR
from app.groups.documents import Group
from app.microservices.documents import Microservice
from app.permissions.documents import Permission
from app.rabbitmq.workers import RegisterMicroserviceWorker
from app.users.documents import User

from amqp_client import AmqpTestClient


USER_PROFILE = 'users.profile'
CREATE_TOKEN = 'json-web-token-api.create-token'

REQUEST_QUEUE = RegisterMicroserviceWorker.QUEUE_NAME
REQUEST_EXCHANGE = RegisterMicroserviceWorker.REQUEST_EXCHANGE_NAME
RESPONSE_EXCHANGE = RegisterMicroserviceWorker.RESPONSE_EXCHANGE_NAME


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
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=create_data)
    await asyncio.sleep(1.0)
    assert len(response.keys()) == 2
    assert EVENT_FIELD_NAME in response.keys()
    assert CONTENT_FIELD_NAME in response.keys()
    assert response[CONTENT_FIELD_NAME] == "OK"

    # Get a new token for the user
    url = sanic_server.app.url_for(CREATE_TOKEN)
    payload = json.dumps({
        "username": "user",
        "password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    tokens = await response.json()
    assert response.status == 201
    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    # And get the user profile with permissions
    url = sanic_server.app.url_for(USER_PROFILE)
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.get(url, headers=headers)
    response_json = await response.json()
    assert response.status == 200
    assert len(response_json.keys()) == 3

    assert 'id' in response_json.keys()
    assert response_json['id'] == str(user.id)

    assert 'username' in response_json.keys()
    assert response_json['username'] == user.username

    assert 'permissions' in response_json.keys()
    assert set(response_json['permissions']) == {'auth.resource.retrieve', 'auth.resource.update'}

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
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=create_data)
    await asyncio.sleep(1.0)
    assert len(response.keys()) == 2
    assert EVENT_FIELD_NAME in response.keys()
    assert CONTENT_FIELD_NAME in response.keys()
    assert response[CONTENT_FIELD_NAME] == "OK"

    # Get a new token for the user
    url = sanic_server.app.url_for(CREATE_TOKEN)
    payload = json.dumps({
        "username": "user",
        "password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    tokens = await response.json()
    assert response.status == 201
    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    # And get the user profile with permissions
    url = sanic_server.app.url_for(USER_PROFILE)
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.get(url, headers=headers)
    response_json = await response.json()
    assert response.status == 200
    assert len(response_json.keys()) == 3

    assert 'id' in response_json.keys()
    assert response_json['id'] == str(user.id)

    assert 'username' in response_json.keys()
    assert response_json['username'] == user.username

    assert 'permissions' in response_json.keys()
    assert set(response_json['permissions']) == {'auth.resource.retrieve', 'auth.resource.update'}

    # Update the existing microservice
    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': [
            {'codename': 'auth.resource.retrieve', 'description': 'get data'},
        ]
    }
    response = await client.send(payload=create_data)
    await asyncio.sleep(1.0)
    assert len(response.keys()) == 2
    assert EVENT_FIELD_NAME in response.keys()
    assert CONTENT_FIELD_NAME in response.keys()
    assert response[CONTENT_FIELD_NAME] == "OK"

    # And check the updates
    url = sanic_server.app.url_for(USER_PROFILE)
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.get(url, headers=headers)
    response_json = await response.json()
    assert response.status == 200
    assert len(response_json.keys()) == 3

    assert 'id' in response_json.keys()
    assert response_json['id'] == str(user.id)

    assert 'username' in response_json.keys()
    assert response_json['username'] == user.username

    assert 'permissions' in response_json.keys()
    assert set(response_json['permissions']) == {'auth.resource.retrieve', }

    await Group.collection.delete_many({})
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})


async def test_user_profile_returns_bad_request_for_missing_authorization_header(sanic_server):
    url = sanic_server.app.url_for(USER_PROFILE)
    response = await sanic_server.get(url)
    response_json = await response.json()

    assert response.status == 400
    assert len(response_json.keys()) == 1

    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == AUTHORIZATION_ERROR

    assert 'message' in error.keys()
    assert error['message'] == "Authorization header isn't set in request."


async def test_user_profile_returns_bad_request_for_invalid_header_prefix(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for(CREATE_TOKEN)
    payload = json.dumps({
        "username": "user",
        "password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    tokens = await response.json()
    assert response.status == 201
    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    url = sanic_server.app.url_for(USER_PROFILE)
    header_token = "NOT_JWT {}".format(tokens["access_token"])
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.get(url, headers=headers, data=payload)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1

    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == HEADER_ERROR

    assert 'message' in error.keys()
    assert error['message'] == 'Before the token necessary to specify the `JWT` prefix.'

    await User.collection.delete_many({})


async def test_user_profile_returns_validation_error_for_invalid_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for(CREATE_TOKEN)
    payload = json.dumps({
        "username": "user",
        "password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    tokens = await response.json()
    assert response.status == 201
    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    url = sanic_server.app.url_for(USER_PROFILE)
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"][:-1]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.get(url, headers=headers)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1

    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == TOKEN_ERROR

    assert 'message' in error.keys()
    assert error['message'] == 'Signature verification failed.'

    await User.collection.delete_many({})


async def test_user_profile_returns_user_wasnot_found_error(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for(CREATE_TOKEN)
    payload = json.dumps({
        "username": "user",
        "password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    tokens = await response.json()
    assert response.status == 201
    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    await User.collection.delete_many({})
    url = sanic_server.app.url_for(USER_PROFILE)
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.get(url, headers=headers)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1
    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == NOT_FOUND_ERROR

    assert 'message' in error.keys()
    assert error['message'] == 'User was not found.'

    await User.collection.delete_many({})


async def test_user_profile_post_not_allowed(sanic_server):
    url = sanic_server.app.url_for(USER_PROFILE)
    response = await sanic_server.post(url)
    assert response.status == 405


async def test_user_profile_patch_not_allowed(sanic_server):
    url = sanic_server.app.url_for(USER_PROFILE)
    response = await sanic_server.patch(url)
    assert response.status == 405


async def test_user_profile_put_not_allowed(sanic_server):
    url = sanic_server.app.url_for(USER_PROFILE)
    response = await sanic_server.put(url)
    assert response.status == 405


async def test_user_profile_delete_not_allowed(sanic_server):
    url = sanic_server.app.url_for(USER_PROFILE)
    response = await sanic_server.delete(url)
    assert response.status == 405
