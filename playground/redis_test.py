import redis


r = redis.Redis.from_url("redis://default:AS4CvtxfimJoIQznO4J7DvZGo1r0T1KcKScv48JXZQSrT6HmEcR1KMo33yrGU6NT@100.121.120.11:55543/00")

r.set("test", "hello")
print(r.get("test").decode("utf-8"))

