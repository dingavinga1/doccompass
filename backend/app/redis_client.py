import redis

from .config import settings


redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def redis_healthcheck() -> bool:
    try:
        return bool(redis_client.ping())
    except Exception:
        return False
