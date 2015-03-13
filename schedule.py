from redis import Redis
from rq import Queue

import os
import urlparse

from text import udacitext

redis_url = os.getenv('REDISTOGO_URL')
if not redis_url:
    raise RuntimeError('Set up Redis To Go first.')

urlparse.uses_netloc.append('redis')
url = urlparse.urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)

queue = Queue(connection=conn)
job = queue.enqueue(udacitext)
