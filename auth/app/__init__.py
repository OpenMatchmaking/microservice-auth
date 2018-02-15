from sanic import Sanic

from app.extensions.redis import RedisExtension
from app.extensions.mongodb import MongoDbExtension


app = Sanic('microservice-auth')
app.config.from_envvar('APP_CONFIG_PATH')

app.redis = RedisExtension(app)
app.mongodb = MongoDbExtension(app)
