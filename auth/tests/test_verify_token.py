import json

from freezegun import freeze_time
from sage_utils.constants import HEADER_ERROR, AUTHORIZATION_ERROR, TOKEN_ERROR
from sage_utils.wrappers import Response

from app.users.documents import User


async def test_verify_token_returns_is_valid_for_correct_access_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
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

    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.post(url, headers=headers)
    response_json = await response.json()
    assert response.status == 200

    assert 'is_valid' in response_json.keys()
    assert response_json['is_valid'] == True

    assert Response.CONTENT_FIELD_NAME in response_json.keys()
    assert response_json[Response.CONTENT_FIELD_NAME] == "OK"

    await User.collection.delete_one({'id': user.id})


async def test_verify_token_return_error_for_a_missing_authorization_header(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    response = await sanic_server.post(url)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 2
    assert 'is_valid' in response_json.keys()
    assert response_json['is_valid'] is False

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    assert Response.CONTENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == AUTHORIZATION_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == "Authorization header isn't set in request."


async def test_verify_token_return_error_for_a_missing_header_prefix(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
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

    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: tokens["access_token"]}
    response = await sanic_server.post(url, headers=headers)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 2
    assert 'is_valid' in response_json.keys()
    assert response_json['is_valid'] is False

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    assert Response.CONTENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == HEADER_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'Before the token necessary to ' \
                                                       'specify the `JWT` prefix.'

    await User.collection.delete_one({'id': user.id})


async def test_verify_token_return_error_for_an_invalid_header_prefix(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
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

    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    header_token = "NOT_JWT {}".format(tokens["access_token"])
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.post(url, headers=headers)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 2
    assert 'is_valid' in response_json.keys()
    assert response_json['is_valid'] is False

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    assert Response.CONTENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == HEADER_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'Before the token necessary to ' \
                                                       'specify the `JWT` prefix.'

    await User.collection.delete_one({'id': user.id})


async def test_verify_token_return_error_for_expired_access_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
    payload = json.dumps({
        "username": "user",
        "password": "123456"
    })

    with freeze_time("2000-01-01"):
        response = await sanic_server.post(url, data=payload)
        tokens = await response.json()

    assert response.status == 201
    assert len(tokens.keys()) == 2
    assert sanic_server.app.config['JWT_ACCESS_TOKEN_FIELD_NAME'] in tokens.keys()
    assert sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME'] in tokens.keys()

    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.post(url, headers=headers)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 2
    assert 'is_valid' in response_json.keys()
    assert response_json['is_valid'] is False

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    assert Response.CONTENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == TOKEN_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'Signature has expired.'

    await User.collection.delete_one({'id': user.id})


async def test_verify_token_return_error_for_invalid_access_token(sanic_server):
    await User.collection.delete_many({})
    user = User(**{"username": "user", "password": "123456"})
    await user.commit()

    url = sanic_server.app.url_for('json-web-token-api.create-token')
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

    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"][:-1]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    response = await sanic_server.post(url, headers=headers)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 2
    assert 'is_valid' in response_json.keys()
    assert response_json['is_valid'] is False

    assert Response.ERROR_FIELD_NAME in response_json.keys()
    assert Response.EVENT_FIELD_NAME not in response_json.keys()
    assert Response.CONTENT_FIELD_NAME not in response_json.keys()
    error = response_json[Response.ERROR_FIELD_NAME]

    assert Response.ERROR_TYPE_FIELD_NAME in error.keys()
    assert error[Response.ERROR_TYPE_FIELD_NAME] == TOKEN_ERROR

    assert Response.ERROR_DETAILS_FIELD_NAME in error.keys()
    assert error[Response.ERROR_DETAILS_FIELD_NAME] == 'Signature verification failed.'

    await User.collection.delete_one({'id': user.id})


async def test_verify_token_get_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    response = await sanic_server.get(url)
    assert response.status == 405


async def test_verify_token_patch_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    response = await sanic_server.patch(url)
    assert response.status == 405


async def test_verify_token_put_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    response = await sanic_server.put(url)
    assert response.status == 405


async def test_verify_token_delete_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.verify-token')
    response = await sanic_server.delete(url)
    assert response.status == 405
