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
APP_PORT = to_int(os.environ.get('APP_HOST', "8000"))
APP_DEBUG = to_bool(os.environ.get('APP_DEBUG', False))
APP_SSL = None
APP_WORKERS = int((os.environ.get('APP_WORKERS', 1)))

SECRET_KEY = os.environ.get('APP_SECRET_KEY', 'some-secret-key')

REDIS_HOST = os.environ.get('REDIS_HOST', "127.0.0.1")
REDIS_PORT = to_int(os.environ.get('REDIS_PORT', "6379"))
REDIS_DATABASE = None
REDIS_SSL = None
REDIS_ENCODING = os.environ.get('REDIS_SSL', None)
REDIS_MIN_SIZE_POOL = to_int(os.environ.get('REDIS_MIN_SIZE_POOL', 1))
REDIS_MAX_SIZE_POOL = to_int(os.environ.get('REDIS_MAX_SIZE_POOL', 10))

MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "user")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD", "password")
MONGODB_HOST = os.environ.get("MONGODB_HOST", "mongodb")
MONGODB_PORT = to_int(os.environ.get("MONGODB_PORT", 27017))
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", None)
MONGODB_URI = 'mongodb://{}:{}@{}:{}/{}'.format(
    MONGODB_USERNAME,
    MONGODB_PASSWORD,
    MONGODB_HOST,
    MONGODB_PORT,
    MONGODB_DATABASE
)
LAZY_UMONGO = MotorAsyncIOInstance()
