import threading


def run_async(func, *args):
    thread = threading.Thread(target=func, args=args, daemon=True)
    thread.start()
    return thread
