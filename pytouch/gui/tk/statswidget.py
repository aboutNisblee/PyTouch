import logging
from datetime import timedelta

from tkinter import font
from tkinter import *
from tkinter import ttk

from pytouch.timer import Timer
from pytouch.trainingmachine import TrainingMachineObserver

logger = logging.getLogger(__name__)


class StatsWidget(TrainingMachineObserver, ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.configure(width=400, height=30)

        self.font = font.Font(family='mono', size=-40)

        self._timer = Timer(10)
        self._timer.on_tick.connect(self._on_tick)

        self._time_string = StringVar(value='00:00.0')
        self._time_label = Label(self, textvariable=self._time_string, font=self.font)

        self._time_label.grid(column=0, row=0, sticky=N + S + W)

    def _on_tick(self, sender, elapsed):
        minutes, seconds = divmod(timedelta.total_seconds(elapsed), 60)
        # FIXME: THIS IS NOT OK!
        # We are updating the gui thread from timer thread!
        # Push it into a queue or build a tkinter based timer.
        self._time_string.set('{minutes:02.0f}:{seconds:02.1f}'.format(minutes=minutes, seconds=seconds))

    def on_pause(self, ctx):
        self._timer.stop()

    def on_unpause(self, ctx):
        self._timer.start()

    def on_restart(self, ctx):
        self._timer.reset()

    def on_miss(self, ctx, index, typed, expected):
        pass

    def on_undo(self, ctx, index, expect):
        pass

    def on_end(self, ctx):
        self._timer.stop()

    def on_hit(self, ctx, index, typed):
        pass
