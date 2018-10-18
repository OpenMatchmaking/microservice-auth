from sanic import Sanic
from sanic.response import text
from sanic_mongodb_ext import MongoDbExtension
from sanic_redis_ext import RedisExtension
from sanic_amqp_ext import AmqpExtension

from app.rabbitmq.workers import RegisterMicroserviceWorker
from app.token.api.workers.generate_token import GenerateTokenWorker
from app.users.api.workers.register_game_client import RegisterGameClientWorker
from app.users.api.workers.user_profile import UserProfileWorker


app = Sanic('microservice-auth')
app.config.from_envvar('APP_CONFIG_PATH')


# Extensions
AmqpExtension(app)
MongoDbExtension(app)
RedisExtension(app)


# RabbitMQ workers
app.amqp.register_worker(RegisterMicroserviceWorker(app))
app.amqp.register_worker(GenerateTokenWorker(app))
app.amqp.register_worker(RegisterGameClientWorker(app))
app.amqp.register_worker(UserProfileWorker(app))


# Public API
async def health_check(request):
    return text('OK')


app.add_route(health_check, '/auth/api/health-check', methods=['GET', ], name='health-check')
