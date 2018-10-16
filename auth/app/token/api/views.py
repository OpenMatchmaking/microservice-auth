from collections import OrderedDict

from bson.objectid import ObjectId
from jwt import InvalidIssuedAtError, ExpiredSignatureError, InvalidTokenError
from sage_utils.constants import VALIDATION_ERROR, NOT_FOUND_ERROR, TOKEN_ERROR
from sage_utils.wrappers import Response
from sanic.response import json

from app.token.exceptions import MissingAccessToken
from app.token.json_web_token import build_payload, generate_token_pair, extract_token, \
    decode_token, extract_and_decode_token, get_redis_key_by_user, generate_access_token
from app.token.redis import get_refresh_token_from_redis
from app.token.api.schemas import LoginSchema, RefreshTokenSchema


async def generate_tokens(request):
    credentials = LoginSchema().load(request.json or {})
    if credentials.errors:
        response = Response.from_error(VALIDATION_ERROR, credentials.errors)
        response.data.pop(Response.EVENT_FIELD_NAME, None)
        return json(response.data, 400)

    username = credentials.data["username"]
    password = credentials.data["password"]

    user_document = request.app.config["LAZY_UMONGO"].User
    user = await user_document.find_one({"username": username})
    if not user or (user and not user.verify_password(password)):
        response = Response.from_error(
            NOT_FOUND_ERROR,
            "User wasn't found or specified an invalid password."
        )
        response.data.pop(Response.EVENT_FIELD_NAME, None)
        return json(response.data, 400)

    payload = build_payload(request.app, extra_data={"user_id": str(user.pk)})
    response = await generate_token_pair(request, payload, user.username)
    return json(response, 201)


async def verify_token(request):
    try:
        raw_access_token = extract_token(request)
    except (MissingAccessToken, InvalidHeaderPrefix) as exc:
        error = exc.details
        error.pop(Response.EVENT_FIELD_NAME, None)
        response = OrderedDict({"is_valid": False})
        response.update(error)
        return json(response, status=exc.status_code)

    secret = request.app.config["JWT_SECRET_KEY"]
    algorithm = request.app.config["JWT_ALGORITHM"]

    error = None
    is_valid = True
    status_code = 200
    try:
        decode_token(raw_access_token, secret, algorithm)
    except (InvalidIssuedAtError, ExpiredSignatureError) as exc:
        is_valid = False
        status_code = 400
        error = Response.from_error(TOKEN_ERROR, str(exc))
    except InvalidTokenError as exc:
        is_valid = False
        status_code = 400
        error = Response.from_error(TOKEN_ERROR, str(exc))

    response = OrderedDict({
        Response.CONTENT_FIELD_NAME: "OK",
        "is_valid": is_valid
    })
    if error:
        error.data.pop(Response.EVENT_FIELD_NAME)
        response.pop(Response.CONTENT_FIELD_NAME, None)
        response.update(error.data)

    return json(response, status=status_code)


async def refresh_token_pairs(request):
    try:
        token = extract_and_decode_token(request)
    except (MissingAuthorizationHeader, InvalidHeaderPrefix) as exc:
        response = exc.details
        response.pop(Response.EVENT_FIELD_NAME, None)
        return json(response, status=exc.status_code)
    except InvalidTokenError as exc:
        response = Response.from_error(TOKEN_ERROR, str(exc))
        response.data.pop(Response.EVENT_FIELD_NAME, None)
        return json(response.data, status=400)

    request_body = RefreshTokenSchema().load(request.json or {})
    if request_body.errors:
        response = Response.from_error(TOKEN_ERROR, request_body.errors)
        response.data.pop(Response.EVENT_FIELD_NAME, None)
        return json(response.data, 400)

    user_id = token.get('user_id', None)
    user_document = request.app.config["LAZY_UMONGO"].User
    user = await user_document.find_one({"_id": ObjectId(user_id)})

    refresh_token = request_body.data['refresh_token'].strip()
    key = get_redis_key_by_user(request, user.username)
    existing_refresh_token = await get_refresh_token_from_redis(request.app.redis, key)

    if not user or (user and existing_refresh_token != refresh_token):
        response = Response.from_error(
            TOKEN_ERROR,
            "User wasn't found or specified an invalid `refresh_token`."
        )
        response.data.pop(Response.EVENT_FIELD_NAME, None)
        return json(response.data, 400)

    secret = request.app.config["JWT_SECRET_KEY"]
    algorithm = request.app.config["JWT_ALGORITHM"]

    payload = build_payload(request.app, extra_data={"user_id": str(user.pk)})
    new_access_token = generate_access_token(payload, secret, algorithm)
    response = {
        request.app.config["JWT_ACCESS_TOKEN_FIELD_NAME"]: new_access_token
    }
    return json(response, 201)
