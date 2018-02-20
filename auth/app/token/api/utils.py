from datetime import datetime, timedelta

from jwt import encode, decode
from passlib.pwd import genword

from app.token.api.exceptions import MissingAuthorizationHeader, InvalidHeaderPrefix


REFRESH_KEY_TEMPLATE = "{prefix}_{username}"


def get_redis_key_by_user(request, username):
    return REFRESH_KEY_TEMPLATE.format(
        prefix=request.app.config["JWT_REFRESH_TOKEN_FIELD_NAME"],
        username=username
    )


async def save_refresh_token_in_redis(redis_pool, key, token):
    with await redis_pool as redis:
        await redis.execute('set', key, token)


async def get_refresh_token_from_redis(redis_pool, key):
    with await redis_pool as redis:
        value = await redis.execute('get', key)
    return value.decode('utf-8')


def build_payload(app, extra_data={}):
    iat = datetime.now()
    exp = iat + timedelta(seconds=app.config.JWT_LIFETIME)
    payload = {
        'iat': iat,
        'exp': exp
    }
    payload.update(extra_data)
    return payload


def generate_access_token(payload, secret, algorithm):
    return encode(payload, secret, algorithm=algorithm)


def generate_refresh_token(length=32, entropy=48):
    return genword(entropy=entropy, length=length, charset="hex")


async def generate_token_pair(request, payload, username):
    secret = request.app.config["JWT_SECRET_KEY"]
    algorithm = request.app.config["JWT_ALGORITHM"]

    access_token = generate_access_token(payload, secret, algorithm)
    refresh_token = generate_refresh_token()

    key = get_redis_key_by_user(request, username)
    await save_refresh_token_in_redis(request.app.redis, key, refresh_token)

    token_pair = {
        request.app.config["JWT_ACCESS_TOKEN_FIELD_NAME"]: access_token,
        request.app.config["JWT_REFRESH_TOKEN_FIELD_NAME"]: refresh_token
    }
    return token_pair


def extract_token(request):
    header_name = request.app.config['JWT_AUTHORIZATION_HEADER_NAME']
    header_prefix = request.app.config['JWT_AUTHORIZATION_HEADER_PREFIX']

    header = request.headers.get(header_name, None)
    if not header:
        raise MissingAuthorizationHeader()

    try:
        prefix, token = header.strip().split(' ')
        if prefix.lower() != header_prefix.lower():
            raise InvalidHeaderPrefix(prefix=header_prefix)
    except ValueError:
        raise InvalidHeaderPrefix(prefix=header_prefix)

    return token


def decode_token(token, secret, algorithm):
    return decode(
        token,
        secret,
        algorithms=[algorithm, ],
        verify=True,
        options={'verify_exp': True}
    )


def extract_and_decode_token(request):
    raw_access_token = extract_token(request)
    secret = request.app.config["JWT_SECRET_KEY"]
    algorithm = request.app.config["JWT_ALGORITHM"]
    return decode_token(raw_access_token, secret, algorithm)
