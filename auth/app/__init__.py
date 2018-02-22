from sanic import Sanic
from sanic.response import text

from app.extensions.amqp import AmqpExtension
from app.extensions.mongodb import MongoDbExtension
from app.extensions.redis import RedisExtension
from app.token.api.blueprints import token_bp
from app.users.api.blueprints import users_bp_v1


app = Sanic('microservice-auth')
app.config.from_envvar('APP_CONFIG_PATH')


# Extensions
AmqpExtension(app)
MongoDbExtension(app)
RedisExtension(app)


# Public API
async def health_check(request):
    return text('OK.')


app.blueprint(token_bp)
app.blueprint(users_bp_v1)
app.add_route(health_check, '/auth/api/health-check', methods=['GET', ], name='health-check')
