import logging
import copy
from datetime import datetime, timedelta
from threading import Thread, Event
from time import sleep

from blinker import Signal

logger = logging.getLogger(__name__)


def timed_sleep(seconds=1):
    """ A recursive version of sleep that guarantees that the sleep time
    is never smaller than requested.

    :param seconds: Seconds to sleep as float
    :return: The drift as float (always negative)
    """
    if seconds <= 0:
        return seconds
    t0 = datetime.utcnow()
    sleep(seconds)
    t1 = datetime.utcnow()
    td = t1 - t0
    if seconds - timedelta.total_seconds(td) > 0:
        logger.warning('wake too early! took', td)
    return timed_sleep(seconds - timedelta.total_seconds(td))


class Timer(object):
    on_tick = Signal()
    on_start = Signal()
    on_stop = Signal()

    def __init__(self, frequence):
        self._freqence = frequence
        self._stop_event = Event()
        self._thread = None
        self._history = list()

    def _run(self, stop_event):
        seconds = 1 / self._freqence
        delta = 0
        while not stop_event.is_set():
            # sleep and compensate the time the callback took
            t0 = datetime.utcnow()
            ts = seconds - delta
            timed_sleep(ts)
            self.on_tick.send(self, elapsed=self.elapsed())
            t1 = datetime.utcnow()
            td = timedelta.total_seconds(t1 - t0)
            delta = td - seconds
            # print('target', ts, 'took', td, 'delta', delta)
        print('stopping timer thread')

    def start(self):
        if self._thread and self._thread.is_alive():
            logger.warning('Timer already running')
            return
        t = datetime.utcnow()
        logger.debug('Starting timer at {}'.format(t.isoformat()))
        self._history.append(('start', t))
        self._stop_event.clear()
        self._thread = Thread(target=self._run, args=(self._stop_event,))
        self._thread.start()

    def stop(self):
        if not self._thread or not self._thread.is_alive():
            logger.warning('Timer not running')
            return
        self._stop_event.set()
        self._thread.join()
        t = datetime.utcnow()
        logger.debug('Stopped timer at {}'.format(t.isoformat()))
        self._history.append(('stop', t))

    def reset(self):
        self.stop()
        self._history.clear()

    def elapsed(self):
        rv = timedelta(0)

        # Make a deep copy of the history and add an artificial stop if we are still running
        history = copy.deepcopy(self._history)
        if history[-1][0] != 'stop':
            history.append(('stop', datetime.utcnow()))

        def pairs(iterable):
            it = iter(iterable)
            return zip(it, it)

        for start, stop in pairs(history):
            rv += (stop[1] - start[1])

        return rv


def test():
    def f(sender, elapsed):
        # print('signal at', elapsed)
        sleep(0.01)
        pass

    t = Timer(100)
    t.on_tick.connect(f)

    for _ in range(3):
        print('starting')
        t.start()
        sleep(5)
        print('stopping')
        t.stop()
        print('elapsed', t.elapsed())


if __name__ == '__main__':
    test()
