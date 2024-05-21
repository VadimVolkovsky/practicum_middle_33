from elasticsearch.exceptions import ConnectionTimeout, ConnectionError as ElasticsearchConnectionError
from redis.exceptions import ConnectionError as RedisConnectionError
from asyncio.exceptions import TimeoutError

CONNECTION_EXCEPTIONS = (ConnectionTimeout, TimeoutError, RedisConnectionError, ElasticsearchConnectionError)

