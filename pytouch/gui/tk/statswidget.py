import copy
import logging
from datetime import timedelta, datetime

from tkinter import font
from tkinter import *
from tkinter import ttk

from pytouch.trainingmachine import TrainingMachineObserver

logger = logging.getLogger(__name__)


class StatsWidget(TrainingMachineObserver, ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.configure(width=400, height=30)

        self.font = font.Font(family='mono', size=-40)

        self._time_string = StringVar(value='00:00.0')
        self._time_label = Label(self, textvariable=self._time_string, font=self.font)

        self._time_label.grid(column=0, row=0, sticky=N + S + W)

        self._after_id = None
        self._pause_history = list()

    def elapsed(self):
        rv = timedelta(0)

        if not self._pause_history:
            return rv

        # Make a deep copy of the history and add an artificial stop if we are still running
        history = copy.deepcopy(self._pause_history)
        if history[-1][0] != 'stop':
            history.append(('stop', datetime.utcnow()))

        def pairs(iterable):
            it = iter(iterable)
            return zip(it, it)

        for start, stop in pairs(history):
            rv += (stop[1] - start[1])

        return rv

    def _on_tick(self):
        self._after_id = self.after(100, self._on_tick)
        minutes, seconds = divmod(timedelta.total_seconds(self.elapsed()), 60)
        self._time_string.set('{minutes:02.0f}:{seconds:02.1f}'.format(minutes=minutes, seconds=seconds))

    def on_unpause(self, ctx):
        if self._after_id is not None:
            logger.warning('Timer already running')
            return
        self._after_id = self.after(100, self._on_tick)
        t = datetime.utcnow()
        logger.debug('Starting timer at {}'.format(t.isoformat()))
        self._pause_history.append(('start', t))

    def on_pause(self, ctx):
        if self._after_id is None:
            logger.warning('Timer not running')
            return
        self.after_cancel(self._after_id)
        self._after_id = None
        t = datetime.utcnow()
        logger.debug('Stopped timer at {}'.format(t.isoformat()))
        self._pause_history.append(('stop', t))

    def on_restart(self, ctx):
        self._pause_history.clear()
        self.after_cancel(self._after_id)
        self._after_id = None

    def on_end(self, ctx):
        self.after_cancel(self._after_id)
        self._after_id = None

    def on_hit(self, ctx, index, typed):
        pass

    def on_miss(self, ctx, index, typed, expected):
        pass

    def on_undo(self, ctx, index, expect):
        pass
