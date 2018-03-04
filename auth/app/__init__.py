from sanic import Sanic
from sanic.response import text
from sanic_mongodb_ext import MongoDbExtension
from sanic_redis_ext import RedisExtension
from sanic_amqp_ext import AmqpExtension

from app.rabbitmq.workers import RegisterMicroserviceWorker
from app.token.api.blueprints import token_bp
from app.users.api.blueprints import users_bp_v1


app = Sanic('microservice-auth')
app.config.from_envvar('APP_CONFIG_PATH')


# Extensions
AmqpExtension(app)
MongoDbExtension(app)
RedisExtension(app)


# RabbitMQ workers
app.amqp.register_worker(RegisterMicroserviceWorker(app))


# Public API
async def health_check(request):
    return text('OK')


app.blueprint(token_bp)
app.blueprint(users_bp_v1)
app.add_route(health_check, '/auth/api/health-check', methods=['GET', ], name='health-check')
