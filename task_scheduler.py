import threading
import time

tasks = []


def add_task(interval, func):
    tasks.append((interval, func, time.time()))


def start_scheduler():
    def loop():
        while True:
            now = time.time()
            for i, (interval, func, last_run) in enumerate(list(tasks)):
                if now - last_run >= interval:
                    try:
                        func()
                    finally:
                        tasks[i] = (interval, func, now)
            time.sleep(1)

    threading.Thread(target=loop, daemon=True).start()
