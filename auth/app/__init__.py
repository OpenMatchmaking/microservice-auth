from sanic import Sanic
from sanic.response import text

from app.extensions.redis import RedisExtension
from app.extensions.mongodb import MongoDbExtension
from app.users.api.blueprints import users_bp_v1

app = Sanic('microservice-auth')
app.config.from_envvar('APP_CONFIG_PATH')

# Extensions
RedisExtension(app)
MongoDbExtension(app)

# Public API
async def heatlh_check(request):
    return text('OK')


app.blueprint(users_bp_v1)
app.add_route(heatlh_check, '/auth/api/health-check', methods=['GET', ])
