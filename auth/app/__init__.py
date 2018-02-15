from sanic import Sanic

from app.extensions.redis import RedisExtension


app = Sanic('microservice-auth')
app.redis = RedisExtension(app)


from sanic import response
@app.route("/")
async def handle(request):
    async with request.app.redis_pool.get() as redis:
        await redis.set('test-my-key', 'value')
        val = await redis.get('test-my-key')
    return response.text(val.decode('utf-8'))
