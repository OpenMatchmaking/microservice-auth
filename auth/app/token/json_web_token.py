from datetime import datetime, timedelta
from typing import Dict

from jwt import encode, decode
from passlib.pwd import genword

from app.token.redis import get_redis_key_by_user, save_refresh_token_in_redis


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


async def generate_token_pair(app, payload, username):
    secret = app.config["JWT_SECRET_KEY"]
    algorithm = app.config["JWT_ALGORITHM"]

    access_token = generate_access_token(payload, secret, algorithm)
    refresh_token = generate_refresh_token()

    key = get_redis_key_by_user(app, username)
    await save_refresh_token_in_redis(app.redis, key, refresh_token)

    return {
        app.config["JWT_ACCESS_TOKEN_FIELD_NAME"]: access_token,
        app.config["JWT_REFRESH_TOKEN_FIELD_NAME"]: refresh_token
    }


def decode_token(token, secret, algorithm):
    return decode(
        token,
        secret,
        algorithms=[algorithm, ],
        verify=True,
        options={'verify_exp': True}
    )


def extract_and_decode_token(app, data: Dict):
    raw_access_token = data.get(app.config['JWT_ACCESS_TOKEN_FIELD_NAME'], '')
    secret = app.config["JWT_SECRET_KEY"]
    algorithm = app.config["JWT_ALGORITHM"]
    return decode_token(raw_access_token, secret, algorithm)
