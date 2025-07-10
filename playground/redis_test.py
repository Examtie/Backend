import redis
import redis.asyncio as redis_async
import asyncio

r2 = redis_async.from_url("redis://default:AS4CvtxfimJoIQznO4J7DvZGo1r0T1KcKScv48JXZQSrT6HmEcR1KMo33yrGU6NT@100.121.120.11:55543/00", decode_responses=True)
#r = redis.Redis.from_url("redis://default:AS4CvtxfimJoIQznO4J7DvZGo1r0T1KcKScv48JXZQSrT6HmEcR1KMo33yrGU6NT@100.121.120.11:55543/00")

async def main():
    await r2.set("test", "hello")
    print(await r2.get("test"))

asyncio.run(main())

