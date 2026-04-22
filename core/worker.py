import queue
import threading
from runtime_utils import log

class TaskQueue:
    """
    Production-grade Async Processing queue for long-running tasks.
    Replaces simple ThreadPools to allow better task management and UI responsiveness.
    """
    def __init__(self):
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def add_task(self, fn, *args, **kwargs):
        log(f"[Queue] Task added: {fn.__name__}")
        self.queue.put((fn, args, kwargs))

    def _worker(self):
        while True:
            fn, args, kwargs = self.queue.get()
            try:
                log(f"[Queue] Executing: {fn.__name__}")
                fn(*args, **kwargs)
            except Exception as e:
                log(f"[Queue] Task failed: {e}")
            finally:
                self.queue.task_done()
