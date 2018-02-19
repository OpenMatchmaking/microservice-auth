from collections import OrderedDict

from bson.objectid import ObjectId
from sanic.response import json
from jwt.exceptions import InvalidIssuedAtError, ExpiredSignatureError, InvalidTokenError

from app.generic.utils import wrap_error
from app.token.api.exceptions import MissingAuthorizationHeader, InvalidHeaderPrefix
from app.token.api.schemas import LoginSchema, RefreshTokenSchema
from app.token.api.utils import build_payload, generate_token_pair, extract_token, \
    decode_token, extract_and_decode_token, get_redis_key_by_user, get_refresh_token_from_redis, \
    generate_access_token


async def generate_tokens(request):
    credentials = LoginSchema().load(request.json or {})
    if credentials.errors:
        return json(wrap_error(credentials.errors), 400)

    username = credentials.data["username"]
    password = credentials.data["password"]

    user_document = request.app.config["LAZY_UMONGO"].User
    user = await user_document.find_one({"username": username})
    if not user or (user and not user.verify_password(password)):
        message = wrap_error("User wasn't found or specified an invalid password.")
        return json(message, 400)

    payload = build_payload(request.app, extra_data={"user_id": str(user.pk)})
    response = await generate_token_pair(request, payload, user.username)
    return json(response, 201)


async def verify_token(request):
    try:
        raw_access_token = extract_token(request)
    except (MissingAuthorizationHeader, InvalidHeaderPrefix) as exc:
        result = OrderedDict({"is_valid": False})
        result.update(exc.details)
        return json(result, status=exc.status_code)

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
        error = wrap_error(str(exc))
    except InvalidTokenError as exc:
        is_valid = False
        status_code = 400
        error = wrap_error(str(exc))

    response = OrderedDict({"is_valid": is_valid})
    if error:
        response.update(error)

    return json(response, status=status_code)


async def refresh_token_pairs(request):
    try:
        token = extract_and_decode_token(request)
    except (MissingAuthorizationHeader, InvalidHeaderPrefix) as exc:
        return json(exc.details, status=exc.status_code)
    except InvalidTokenError as exc:
        return json(wrap_error(str(exc)), status=400)

    request_body = RefreshTokenSchema().load(request.json or {})
    if request_body.errors:
        return json(wrap_error(request_body.errors), 400)

    user_id = token.get('user_id', None)
    user_document = request.app.config["LAZY_UMONGO"].User
    user = await user_document.find_one({"_id": ObjectId(user_id)})

    refresh_token = request_body.data['refresh_token'].strip()
    key = get_redis_key_by_user(request, user.username)
    existing_refresh_token = await get_refresh_token_from_redis(request.app.redis, key)

    if not user or (user and existing_refresh_token != refresh_token):
        message = wrap_error("User wasn't found or specified an invalid `refresh_token`.")
        return json(message, 400)

    secret = request.app.config["JWT_SECRET_KEY"]
    algorithm = request.app.config["JWT_ALGORITHM"]

    payload = build_payload(request.app, extra_data={"user_id": str(user.pk)})
    new_access_token = generate_access_token(payload, secret, algorithm)
    response = {
        request.app.config["JWT_ACCESS_TOKEN_FIELD_NAME"]: new_access_token
    }
    return json(response, 201)
