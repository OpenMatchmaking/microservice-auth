REFRESH_KEY_TEMPLATE = "{prefix}_{username}"


def get_redis_key_by_user(app, username):
    return REFRESH_KEY_TEMPLATE.format(
        prefix=app.config["JWT_REFRESH_TOKEN_FIELD_NAME"],
        username=username
    )


async def get_refresh_token_from_redis(redis_pool, key):
    with await redis_pool as redis:
        value = await redis.execute('get', key)
    return value.decode('utf-8')


async def save_refresh_token_in_redis(redis_pool, key, token):
    with await redis_pool as redis:
        await redis.execute('set', key, token)
