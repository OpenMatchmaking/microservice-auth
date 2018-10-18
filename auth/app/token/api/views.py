from bson.objectid import ObjectId
from jwt import InvalidIssuedAtError, ExpiredSignatureError, InvalidTokenError
from sage_utils.constants import VALIDATION_ERROR, NOT_FOUND_ERROR, TOKEN_ERROR
from sage_utils.wrappers import Response
from sanic.response import json

from app.token.json_web_token import build_payload, extract_token, \
    extract_and_decode_token, get_redis_key_by_user, generate_access_token
from app.token.redis import get_refresh_token_from_redis
from app.token.api.schemas import RefreshTokenSchema


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
