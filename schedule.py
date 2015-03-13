from rq import Queue

from text import udacitext
from worker import conn

queue = Queue(connection=conn)
job = queue.enqueue(udacitext)
