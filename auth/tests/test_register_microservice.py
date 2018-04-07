import asyncio
from copy import deepcopy

from sage_utils.constants import VALIDATION_ERROR
from sage_utils.wrappers import Response

from app.groups.documents import Group
from app.microservices.documents import Microservice
from app.permissions.documents import Permission
from app.rabbitmq.workers import RegisterMicroserviceWorker

from amqp_client import AmqpTestClient


REQUEST_QUEUE = RegisterMicroserviceWorker.QUEUE_NAME
REQUEST_EXCHANGE = RegisterMicroserviceWorker.REQUEST_EXCHANGE_NAME
RESPONSE_EXCHANGE = RegisterMicroserviceWorker.RESPONSE_EXCHANGE_NAME


async def test_register_microservice_returns_validation_error_for_missing_fields(sanic_server):
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload={})

    assert len(response.keys()) == 2
    assert Response.ERROR_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error["type"] == VALIDATION_ERROR

    assert 'message' in error.keys()
    assert len(error['message'].keys()) == 2

    assert 'name' in error['message'].keys()
    assert len(error['message']['name']) == 1
    assert error['message']['name'][0] == 'Missing data for required field.'

    assert 'version' in error['message'].keys()
    assert len(error['message']['version']) == 1
    assert error['message']['version'][0] == 'Missing data for required field.'


async def test_register_microservice_returns_validation_error_for_invalid_data(sanic_server):
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=b'INVALID_DATA', raw_data=True)

    assert len(response.keys()) == 2
    assert Response.ERROR_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == VALIDATION_ERROR

    assert 'message' in error.keys()
    assert len(error['message'].keys()) == 2

    assert 'name' in error['message'].keys()
    assert len(error['message']['name']) == 1
    assert error['message']['name'][0] == 'Missing data for required field.'

    assert 'version' in error['message'].keys()
    assert len(error['message']['version']) == 1
    assert error['message']['version'][0] == 'Missing data for required field.'


async def test_register_microservice_returns_validation_error_for_invalid_version(sanic_server):
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    create_data = {
        'name': 'auth',
        'version': 'v1.0',
        'permissions': []
    }
    response = await client.send(payload=create_data)

    assert len(response.keys()) == 2
    assert Response.ERROR_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == VALIDATION_ERROR

    assert 'message' in error.keys()
    assert len(error['message'].keys()) == 1

    assert 'version' in error['message'].keys()
    assert len(error['message']['version']) == 1
    assert error['message']['version'][0] == "Field value must match the " \
                                             "`major.minor.patch` version semantics."


async def test_register_microservice_creates_new_microservice_with_permissions(sanic_server):
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})

    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': [
            {'codename': 'auth.test.permissions-one', 'description': 'description'},
            {'codename': 'auth.test.permissions-two'},
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
    instance = await Microservice.collection.find_one({'name': create_data['name']})

    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()

    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    assert instance['name'] == create_data['name']
    assert instance['version'] == create_data['version']
    assert len(instance['permissions']) == 2

    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})


async def test_register_microservice_returns_validation_error_for_invalid_permissions(sanic_server):  # NOQA
    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': [{'description': 'a permission without name'}]
    }
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=create_data)

    assert len(response.keys()) == 2
    assert Response.ERROR_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert "type" in error.keys()
    assert error["type"] == VALIDATION_ERROR

    assert 'message' in error.keys()
    assert len(error['message'].keys()) == 1

    assert 'permissions' in error["message"].keys()
    assert len(error["message"]['permissions']) == 1
    assert len(error["message"]['permissions']['0']) == 1
    assert 'codename' in error["message"]['permissions']['0'].keys()
    assert len(error["message"]['permissions']['0']['codename']) == 1
    assert error["message"]['permissions']['0']['codename'][0] == 'Not a valid string.'


async def test_register_microservice_returns_validation_error_for_invalid_codename_format(sanic_server):  # NOQA
    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': [
            {'codename': 'codename_is_invalid', 'descriptions': 'a permission without name'}
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

    assert len(response.keys()) == 2
    assert Response.ERROR_FIELD_NAME in response.keys()
    error = response[Response.ERROR_FIELD_NAME]

    assert "type" in error.keys()
    assert error["type"] == VALIDATION_ERROR

    assert 'message' in error.keys()
    assert len(error['message'].keys()) == 1

    assert 'permissions' in error["message"].keys()
    assert len(error["message"]['permissions']) == 1
    assert len(error["message"]['permissions']['0']) == 1
    assert 'codename' in error["message"]['permissions']['0'].keys()
    assert len(error["message"]['permissions']['0']['codename']) == 1
    assert error["message"]['permissions']['0']['codename'][0] == "Field value can contain " \
                                                                  "only 'a'-'z', '.', '-' " \
                                                                  "characters."


async def test_register_microservice_creates_new_microservice_without_permissions(sanic_server):
    await Microservice.collection.delete_many({})

    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': []
    }
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=create_data)
    instance = await Microservice.collection.find_one({'name': create_data['name']})

    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()

    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    assert instance['name'] == create_data['name']
    assert instance['permissions'] == create_data['permissions']
    assert instance['version'] == create_data['version']

    await Microservice.collection.delete_many({})


async def test_register_microservice_updates_existing_microservice(sanic_server):
    create_data = {
        'name': 'auth',
        'version': '1.0.0',
        'permissions': []
    }
    await Microservice.collection.delete_many({})
    old_instance = Microservice(**create_data)
    await old_instance.commit()

    update_data = deepcopy(create_data)
    update_data['version'] = '2.0.0'
    client = AmqpTestClient(
        sanic_server.server.app,
        routing_key=REQUEST_QUEUE,
        request_exchange=REQUEST_EXCHANGE,
        response_queue='',
        response_exchange=RESPONSE_EXCHANGE
    )
    response = await client.send(payload=update_data)
    new_instance = await Microservice.collection.find_one({'name': create_data['name']})

    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()

    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    assert old_instance.version != new_instance['version']
    assert new_instance['version'] == update_data['version']

    await Microservice.collection.delete_many({})


async def test_register_microservice_synchronize_new_permissions_for_game_client_group(sanic_server):  # NOQA
    for group_name, config in sanic_server.app.config['DEFAULT_GROUPS'].items():
        data = {'name': group_name}
        data.update(config.get('init', {}))
        await Group(**data).commit()
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})

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
    microservice = await Microservice.collection.find_one({'name': create_data['name']})
    await asyncio.sleep(1.0)

    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()

    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    assert microservice['name'] == create_data['name']
    assert microservice['version'] == create_data['version']
    assert len(microservice['permissions']) == 2

    permissions = await Permission.collection\
        .find({"_id": {"$in": [obj for obj in microservice['permissions']]}})\
        .to_list(10)
    permission_codenames = [perm['codename'] for perm in permissions]

    assert len(permission_codenames) == 2
    assert create_data['permissions'][0]['codename'] in permission_codenames
    assert create_data['permissions'][1]['codename'] in permission_codenames

    groups = await Group.collection\
        .find({"name": "Game client"}) \
        .collation({"locale": "en", "strength": 2}) \
        .to_list(1)
    game_client_group = groups[0] if groups else None

    assert len(microservice['permissions']) == len(game_client_group['permissions'])

    await Group.collection.delete_many({})
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})


async def test_register_microservice_synchronize_deleted_permissions_for_game_client_group(sanic_server):  # NOQA
    for group_name, config in sanic_server.app.config['DEFAULT_GROUPS'].items():
        data = {'name': group_name}
        data.update(config.get('init', {}))
        await Group(**data).commit()
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})

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
    microservice = await Microservice.collection.find_one({'name': create_data['name']})

    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()

    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    assert microservice['name'] == create_data['name']
    assert microservice['version'] == create_data['version']
    assert len(microservice['permissions']) == 2

    permissions = await Permission.collection\
        .find({"_id": {"$in": [obj for obj in microservice['permissions']]}})\
        .to_list(10)
    permission_codenames = [perm['codename'] for perm in permissions]

    assert len(permission_codenames) == 2
    assert create_data['permissions'][0]['codename'] in permission_codenames
    assert create_data['permissions'][1]['codename'] in permission_codenames

    groups = await Group.collection\
        .find({"name": "Game client"}) \
        .collation({"locale": "en", "strength": 2}) \
        .to_list(1)
    game_client_group = groups[0] if groups else None

    assert len(microservice['permissions']) == len(game_client_group['permissions'])

    # Remove permission for the existing microservice and related groups
    update_data = deepcopy(create_data)
    update_data['permissions'] = update_data['permissions'][:1]
    response = await client.send(payload=update_data)

    assert len(response.keys()) == 2
    assert Response.EVENT_FIELD_NAME in response.keys()

    assert Response.CONTENT_FIELD_NAME in response.keys()
    assert response[Response.CONTENT_FIELD_NAME] == "OK"

    await asyncio.sleep(1.0)
    microservice = await Microservice.collection.find_one({'name': update_data['name']})
    assert microservice['name'] == update_data['name']
    assert microservice['version'] == update_data['version']
    assert len(microservice['permissions']) == 1

    permissions = await Permission.collection \
        .find({"_id": {"$in": [obj for obj in microservice['permissions']]}}) \
        .to_list(10)
    permission_codenames = [perm['codename'] for perm in permissions]

    assert len(permission_codenames) == 1
    assert update_data['permissions'][0]['codename'] in permission_codenames

    groups = await Group.collection \
        .find({"name": "Game client"}) \
        .collation({"locale": "en", "strength": 2}) \
        .to_list(1)
    game_client_group = groups[0] if groups else None

    assert len(microservice['permissions']) == len(game_client_group['permissions'])

    await Group.collection.delete_many({})
    await Permission.collection.delete_many({})
    await Microservice.collection.delete_many({})
