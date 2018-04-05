import json

from app.generic.utils import ERROR_FIELD_NAME, EVENT_FIELD_NAME, AUTHORIZATION_ERROR, \
    HEADER_ERROR, TOKEN_ERROR
from app.users.documents import User


async def test_refresh_token_returns_new_access_token(sanic_server):
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

    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    refresh_token = tokens[sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']]
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    payload = json.dumps({
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: refresh_token
    })
    response = await sanic_server.post(url, headers=headers, data=payload)
    response_json = await response.json()
    assert response.status == 201
    assert 'access_token' in response_json.keys()

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_returns_error_for_a_missing_authorization_header(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    response = await sanic_server.post(url)
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


async def test_refresh_token_return_error_for_a_missing_header_prefix(sanic_server):
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

    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    refresh_token = tokens[sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']]
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: tokens["access_token"]}
    payload = json.dumps({
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: refresh_token
    })
    response = await sanic_server.post(url, headers=headers, data=payload)
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

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_return_error_for_an_invalid_header_prefix(sanic_server):
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

    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    refresh_token = tokens[sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']]
    header_token = "NOT_JWT {}".format(tokens["access_token"])
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    payload = json.dumps({
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: refresh_token
    })
    response = await sanic_server.post(url, headers=headers, data=payload)
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

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_return_error_for_an_invalid_access_token(sanic_server):
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

    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    refresh_token = tokens[sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']]
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"][:-1]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    payload = json.dumps({
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: refresh_token
    })
    response = await sanic_server.post(url, headers=headers, data=payload)
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

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_return_error_for_a_missing_refresh_token(sanic_server):
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

    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    payload = json.dumps({})
    response = await sanic_server.post(url, headers=headers, data=payload)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1
    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == TOKEN_ERROR

    assert 'message' in error.keys()
    assert len(error['message']) == 1

    assert 'refresh_token' in error['message'].keys()
    assert len(error['message']['refresh_token']) == 1
    assert error['message']['refresh_token'][0] == 'Missing data for required field.'

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_return_error_for_an_refresh_token(sanic_server):
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

    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    header_token = "{} {}".format(
        sanic_server.app.config['JWT_AUTHORIZATION_HEADER_PREFIX'],
        tokens["access_token"]
    )
    headers = {sanic_server.app.config['JWT_AUTHORIZATION_HEADER_NAME']: header_token}
    payload = json.dumps({
        sanic_server.app.config['JWT_REFRESH_TOKEN_FIELD_NAME']: "INVALID_REFRESH_TOKEN"
    })
    response = await sanic_server.post(url, headers=headers, data=payload)
    response_json = await response.json()
    assert response.status == 400
    assert len(response_json.keys()) == 1
    assert ERROR_FIELD_NAME in response_json.keys()
    assert EVENT_FIELD_NAME not in response_json.keys()
    error = response_json[ERROR_FIELD_NAME]

    assert 'type' in error.keys()
    assert error['type'] == TOKEN_ERROR

    assert 'message' in error.keys()
    assert error['message'] == "User wasn't found or specified an invalid `refresh_token`."

    await User.collection.delete_one({'id': user.id})


async def test_refresh_token_get_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    response = await sanic_server.get(url)
    assert response.status == 405


async def test_refresh_token_patch_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    response = await sanic_server.patch(url)
    assert response.status == 405


async def test_refresh_token_put_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    response = await sanic_server.put(url)
    assert response.status == 405


async def test_refresh_token_delete_not_allowed(sanic_server):
    url = sanic_server.app.url_for('json-web-token-api.refresh-token')
    response = await sanic_server.delete(url)
    assert response.status == 405
