from sanic import Sanic

from app.extensions.redis import RedisExtension


app = Sanic('microservice-auth')
app.config.from_envvar('APP_CONFIG_PATH')
app.redis = RedisExtension(app)


from sanic import response

@app.route("/")
async def handle(request):
    with await request.app.redis as redis:
        await redis.set('test-my-key', 'value')
        val = await redis.get('test-my-key')
    return response.text(val.decode('utf-8'))

