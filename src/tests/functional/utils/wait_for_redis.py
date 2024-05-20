import time

from redis import Redis

from tests.functional.settings import test_settings


if __name__ == '__main__':
    redis = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    while True:
        if redis.ping():
            break
        time.sleep(1)
