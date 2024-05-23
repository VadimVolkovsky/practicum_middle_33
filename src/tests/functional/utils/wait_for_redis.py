import logging
import os

from redis import Redis

from tests.functional.settings import test_settings

logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def main():
    redis = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    if redis.ping():
        logger.info("Redis connection OK")
        return
    else:
        logger.info("Waiting for connection to Redis...")
        raise ConnectionError


if __name__ == '__main__':
    main()
