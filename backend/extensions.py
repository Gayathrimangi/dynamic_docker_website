import redis
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()
redis_client = None

def init_redis(app):
    global redis_client
    if app.config.get("REDIS_URL"):
        redis_client = redis.Redis.from_url(
            app.config["REDIS_URL"],
            decode_responses=True
        )
    else:
        redis_client = redis.Redis(
            host=app.config.get("REDIS_HOST", "localhost"),
            port=app.config.get("REDIS_PORT", 6379),
            password=app.config.get("REDIS_PASSWORD") or None,
            db=app.config.get("REDIS_DB", 0),
            decode_responses=True
        )
    return redis_client

def get_redis():
    global redis_client
    return redis_client
