import os

from umongo import MotorAsyncIOInstance


def to_bool(value):
    return str(value).strip().lower() in ['1', 'true', 'yes']


def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


APP_HOST = os.environ.get('APP_HOST', "127.0.0.1")
APP_PORT = to_int(os.environ.get('APP_HOST', "80"))
APP_DEBUG = to_bool(os.environ.get('APP_DEBUG', False))
APP_WORKERS = int((os.environ.get('APP_WORKERS', 1)))
APP_SSL_CERT = os.environ.get('APP_SSL_CERT', None)
APP_SSL_KEY = os.environ.get('APP_SSL_KEY', None)
if APP_SSL_CERT and APP_SSL_KEY:
    APP_SSL = {"cert": APP_SSL_CERT, "key": APP_SSL_KEY}
else:
    APP_SSL = None

# Redis settings
REDIS_HOST = os.environ.get('REDIS_HOST', "127.0.0.1")
REDIS_PORT = to_int(os.environ.get('REDIS_PORT', "6379"))
REDIS_DATABASE = os.environ.get('REDIS_DATABASE', None)
REDIS_SSL = False
REDIS_ENCODING = os.environ.get('REDIS_ENCODING', None)
REDIS_MIN_SIZE_POOL = to_int(os.environ.get('REDIS_MIN_SIZE_POOL', 1))
REDIS_MAX_SIZE_POOL = to_int(os.environ.get('REDIS_MAX_SIZE_POOL', 10))

# MongoDB settings
MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "user")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "password")
MONGODB_HOST = os.environ.get("MONGODB_HOST", "mongodb")
MONGODB_PORT = to_int(os.environ.get("MONGODB_PORT", 27017))
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "")
MONGODB_URI = 'mongodb://{}:{}@{}:{}/{}'.format(
    MONGODB_USERNAME,
    MONGODB_PASSWORD,
    MONGODB_HOST,
    MONGODB_PORT,
    MONGODB_DATABASE
)
LAZY_UMONGO = MotorAsyncIOInstance()

# AMQP settings
AMQP_USERNAME = os.environ.get("AMQP_USERNAME", "user")
AMQP_PASSWORD = os.environ.get("AMQP_PASSWORD", "password")
AMQP_HOST = os.environ.get("AMQP_HOST", "rabbitmq")
AMQP_PORT = to_int(os.environ.get("AMQP_PORT", 5672))
AMQP_VIRTUAL_HOST = os.environ.get("AMQP_VIRTUAL_HOST", "vhost")
AMQP_USING_SSL = to_bool(os.environ.get("AMQP_USING_SSL", False))

# Settings for setting up JWT
JWT_ALGORITHM = 'HS256'
JWT_LIFETIME = 60 * 30
JWT_SECRET_KEY = os.environ.get('APP_JWT_SECRET_KEY', 'some-secret-key')
JWT_ACCESS_TOKEN_FIELD_NAME = 'access_token'
JWT_REFRESH_TOKEN_FIELD_NAME = 'refresh_token'

# Settings for tests
TEST_MONGODB_USERNAME = os.environ.get("TEST_MONGODB_USERNAME", "root")
TEST_MONGODB_PASSWORD = os.environ.get("TEST_MONGODB_PASSWORD", "root")
TEST_MONGODB_HOST = os.environ.get("MONGODB_HOST", "mongodb")
TEST_MONGODB_PORT = to_int(os.environ.get("MONGODB_PORT", 27017))
TEST_MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", 'test_database')
TEST_MONGODB_URI = 'mongodb://{}:{}@{}:{}/'.format(
    TEST_MONGODB_USERNAME,
    TEST_MONGODB_PASSWORD,
    TEST_MONGODB_HOST,
    TEST_MONGODB_PORT,
    TEST_MONGODB_DATABASE
)

TEST_REDIS_HOST = os.environ.get('TEST_REDIS_HOST', "redis")
TEST_REDIS_PORT = to_int(os.environ.get('TEST_REDIS_PORT', "6379"))
TEST_REDIS_DATABASE = os.environ.get('TEST_REDIS_DATABASE', 1)
TEST_REDIS_SSL = None
TEST_REDIS_ENCODING = os.environ.get('TEST_REDIS_ENCODING', None)
TEST_REDIS_MIN_SIZE_POOL = to_int(os.environ.get('TEST_REDIS_MIN_SIZE_POOL', 1))
TEST_REDIS_MAX_SIZE_POOL = to_int(os.environ.get('TEST_REDIS_MAX_SIZE_POOL', 10))

# Application settings
# `filter` key is a part of match expression for a MongoDB aggregation query, that will be
# used for resolving which permissions are necessary to set to the certain group.
# For more details read: https://docs.mongodb.com/manual/reference/operator/aggregation/match/
DEFAULT_GROUPS = {
    "Game client": {
        "init": {"permissions": []},
        "filter": {
            "$or": [
                {"codename": {"$regex": ".retrieve$"}},
                {"codename": {"$regex": ".update$"}},
            ]
        }
    }
}
