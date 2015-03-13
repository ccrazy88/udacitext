from redis import Redis
from rq import Queue

from text import udacitext

queue = Queue(connection=Redis())
job = queue.enqueue(udacitext)
