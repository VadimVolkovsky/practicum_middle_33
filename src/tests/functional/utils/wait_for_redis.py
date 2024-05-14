import time

from redis import Redis
# from core.config import app_settings


if __name__ == '__main__':
    redis = Redis(host='redis', port=6379)  # TODO вынести в окружение
    while True:
        if redis.ping():
            break
        time.sleep(1)
