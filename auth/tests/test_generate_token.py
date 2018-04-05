import json

from app.generic.utils import ERROR_FIELD_NAME, EVENT_FIELD_NAME, NOT_FOUND_ERROR, \
    VALIDATION_ERROR
from app.users.documents import User


async def test_generate_token_returns_a_new_token_pair(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
    payload = json.dumps({
        "username": "user",
        "password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    response_json = await response.json()
    assert response.status == 201

    assert len(response_json.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in response_json.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in response_json.keys()

    await User.collection.delete_one({'id': user.id})


async def test_generate_token_returns_error_for_an_invalid_username(sanic_server):
    await User.collection.delete_many({})
    await User(**{"username": "user", "password": "123456"}).commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
    payload = json.dumps({
        "username": "NON_EXISTING_USER",
        "password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1
    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == NOT_FOUND_ERROR

    assert 'message' in error.keys()
    assert error['message'] == "User wasn't found or specified an invalid password."

    await User.collection.delete_many({})


async def test_generate_token_returns_error_for_an_invalid_password(sanic_server):
    await User.collection.delete_many({})
    await User(**{"username": "user", "password": "123456"}).commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
    payload = json.dumps({
        "username": "user",
        "password": "WRONG_PASSWORD"
    })
    response = await sanic_server.post(url, data=payload)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1
    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == NOT_FOUND_ERROR

    assert 'message' in error.keys()
    assert error['message'] == "User wasn't found or specified an invalid password."

    await User.collection.delete_many({})


async def test_generate_token_returns_validation_error_for_empty_body(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.create-token')
    response = await sanic_server.post(url)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1
    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]
    assert len(error.keys()) == 2

    assert 'type' in error.keys()
    assert error["type"] == VALIDATION_ERROR

    assert 'message' in error.keys()
    assert len(error['message'].keys()) == 2

    assert 'username' in error['message'].keys()
    assert len(error['message']['username']) == 1
    assert error['message']['username'][0] == 'Missing data for required field.'

    assert 'password' in error['message'].keys()
    assert len(error['message']['password']) == 1
    assert error['message']['password'][0] == 'Missing data for required field.'


async def test_generate_token_get_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.create-token')
    response = await sanic_server.get(url)
    assert response.status == 405


async def test_generate_token_patch_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.create-token')
    response = await sanic_server.patch(url)
    assert response.status == 405


async def test_generate_token_put_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.create-token')
    response = await sanic_server.put(url)
    assert response.status == 405


async def test_generate_token_delete_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.create-token')
    response = await sanic_server.delete(url)
    assert response.status == 405
