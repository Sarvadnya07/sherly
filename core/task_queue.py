import threading
from queue import Queue

queue = Queue()


def _worker():
    while True:
        func, args = queue.get()
        try:
            func(*args)
        finally:
            queue.task_done()


threading.Thread(target=_worker, daemon=True).start()


def add_task(func, *args):
    queue.put((func, args))
