import concurrent
from concurrent.futures._base import Executor


def wait_for_futures(executor: Executor, futures: list):
    try:
        for f in futures:
            f.result()
    except KeyboardInterrupt as e:
        # This secretly assassinates our threads. The assassin isn't very good though because it
        # relies on our process dieing for the threads to go out. If someone catches the exception
        # and keeps doing work, the homicides won't happen until that work is finished.
        executor._threads.clear()
        concurrent.futures.thread._threads_queues.clear()
        raise e
