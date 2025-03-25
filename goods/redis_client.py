import redis
from urllib.parse import urlparse
from django.conf import settings


def get_redis_client():
    cache_config = settings.CACHES['default']
    location = cache_config['LOCATION']
    if location.startswith('redis://') or location.startswith('rediss://'):
        # 解析 URL
        parsed = urlparse(location)
        host = parsed.hostname
        port = parsed.port or 6379
        db = parsed.path.lstrip('/') or '0'
        db = int(db) if db.isdigit() else 0
        password = parsed.password
    else:
        raise ValueError("Unsupported Redis LOCATION format")
    redis_client = redis.Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        decode_responses=True,  # 如果希望返回的值为字符串而不是字节，可以设置 decode_responses=True
    )
    return redis_client
