from sanic import Sanic

from app.extensions.redis import RedisExtension
from app.extensions.mongodb import MongoDbExtension
from app.users.api.blueprints import users_bp_v1

app = Sanic('microservice-auth')
app.config.from_envvar('APP_CONFIG_PATH')

# Extensions
RedisExtension(app)
MongoDbExtension(app)

# Public API
app.blueprint(users_bp_v1)
