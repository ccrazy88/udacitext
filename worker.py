from redis import Redis
from rq import Worker, Queue, Connection
import os
import urlparse


listen = ["high", "default", "low"]
urlparse.uses_netloc.append("redis")
redis_url = os.getenv("REDISTOGO_URL", "redis://localhost:6379")
url = urlparse.urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)


if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
