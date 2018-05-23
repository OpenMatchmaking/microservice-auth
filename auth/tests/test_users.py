import json

from sage_utils.constants import VALIDATION_ERROR
from sage_utils.wrappers import Response

from app.users.documents import User


async def test_users_post_successfully_creates_a_new_user(sanic_server):
    await User.collection.delete_many({})

    url = sanic_server.app.url_for('users.game-client-register')
    payload = json.dumps({
        "username": "new_user",
        "password": "123456",
        "confirm_password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    response_json = await response.json()
    assert response.status == 201
    assert len(response_json.keys()) == 2
    assert "id" in response_json
    assert "username" in response_json

    await User.collection.delete_one({'id': response_json['id']})


async def test_users_post_returns_validation_error_for_non_unique_username(sanic_server):
    await User.collection.delete_many({})
    await User(**{"username": "new_user", "password": "123456"}).commit()

    url = sanic_server.app.url_for('users.game-client-register')
    payload = json.dumps({
        "username": "new_user",
        "password": "123456",
        "confirm_password": "123456"
    })
    response = await sanic_server.post(url, data=payload)
    response_json = await response.json()
    assert response.status == 400

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == VALIDATION_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME].keys()) == 1

    assert 'username' in error[Response.ERROR_DETAILS_FIELD_NAME]
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME]['username']) == 1
    assert error[Response.ERROR_DETAILS_FIELD_NAME]['username'][0] == 'Username must be unique.'

    await User.collection.delete_many({})


async def test_users_post_returns_validation_error_for_not_matched_password(sanic_server):
    url = sanic_server.app.url_for('users.game-client-register')
    payload = json.dumps({
        "username": "new_user",
        "password": "123456",
        "confirm_password": "ANOTHER_PASSWORD"
    })
    response = await sanic_server.post(url, data=payload)
    response_json = await response.json()
    assert response.status == 400

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == VALIDATION_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert len(error[Response.ERROR_DETAILS_FIELD_NAME].keys()) == 1

    details = error[Response.ERROR_DETAILS_FIELD_NAME]
    assert 'confirm_password' in details.keys()
    assert len(details['confirm_password']) == 1
    assert details['confirm_password'][0] == 'Confirm password must equal to a new password.'


async def test_users_post_returns_validation_error_for_missing_fields(sanic_server):
    url = sanic_server.app.url_for('users.game-client-register')
    payload = json.dumps({})
    response = await sanic_server.post(url, data=payload)
    response_json = await response.json()
    assert response.status == 400

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

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


async def test_users_get_not_allowed(sanic_server):
    url = sanic_server.app.url_for('users.game-client-register')
    response = await sanic_server.get(url)
    assert response.status == 405


async def test_users_patch_not_allowed(sanic_server):
    url = sanic_server.app.url_for('users.game-client-register')
    response = await sanic_server.patch(url)
    assert response.status == 405


async def test_users_put_not_allowed(sanic_server):
    url = sanic_server.app.url_for('users.game-client-register')
    response = await sanic_server.put(url)
    assert response.status == 405


async def test_users_delete_not_allowed(sanic_server):
    url = sanic_server.app.url_for('users.game-client-register')
    response = await sanic_server.delete(url)
    assert response.status == 405
