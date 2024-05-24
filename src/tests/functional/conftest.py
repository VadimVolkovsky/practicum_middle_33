pytest_plugins = (
    'tests.functional.pytest_fixtures.api',
    'tests.functional.pytest_fixtures.connections',
    'tests.functional.pytest_fixtures.elasticsearch',
)


# @pytest_asyncio.fixture
# async def redis_pool():
#     pool = await aioredis.create_redis_pool(
#         (Setting.REDIS_HOST, Setting.REDIS_PORT), minsize=5, maxsize=10,
#     )
#     yield pool
#     pool.close()
#     await pool.wait_closed()
