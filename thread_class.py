import threading


# for stoppable thread
# for thread thread
# parent class
class ThreadClass(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    _stop_event = None

    def __init__(self):
        super(ThreadClass, self).__init__()
        self._stop_event = threading.Event()

    def terminate(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.isSet()
