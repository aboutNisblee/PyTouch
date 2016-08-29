import copy
import logging
from datetime import timedelta, datetime

from tkinter import font
from tkinter import *
from tkinter import ttk

import pytouch.trainingmachine as tm

logger = logging.getLogger(__name__)

ZERO = '00:00.0'


class Element(ttk.Frame):
    def __init__(self, master, title, main, sub, **kwargs):
        super().__init__(master=master, **kwargs)

        self.configure(borderwidth=3, relief='groove')

        self._title_font = font.Font(family='mono', size=-15)
        self._main_font = font.Font(family='mono', size=-30, weight='bold')
        self._sub_font = font.Font(family='mono', size=-15)

        self._title_string = StringVar(value=title)
        self._title_label = ttk.Label(self, textvariable=self._title_string, font=self._title_font)
        self._main_string = StringVar(value=main)
        self._main_label = ttk.Label(self, textvariable=self._main_string, font=self._main_font)
        self._sub_string = StringVar(value=sub)
        self._sub_label = ttk.Label(self, textvariable=self._sub_string, font=self._sub_font)

        self._title_label.grid(column=0, row=0, sticky=N + S + W, padx=15, pady=5)
        self._main_label.grid(column=0, row=1, sticky=N + S + W, padx=10, pady=5)
        self._sub_label.grid(column=0, row=2, sticky=N + S + W, padx=15, pady=5)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    @property
    def main(self):
        return self._main_string.get()

    @main.setter
    def main(self, value):
        self._main_string.set(value)

    @property
    def sub(self):
        return self._sub_string.get()

    @sub.setter
    def sub(self, value):
        self._sub_string.set(value)

    @property
    def text_width(self):
        # FIXME: This isn't working!
        return max(
            self._title_font.measure(self._title_label.cget('text')) + 2 * 15,
            self._main_font.measure(self._main_label.cget('text')) + 2 * 10,
            self._sub_font.measure(self._sub_label.cget('text')) + 2 * 15,
        )


class TimeElement(Element):
    def __init__(self, master, **kwargs):
        super().__init__(master, 'Elapsed time', ZERO, ZERO, **kwargs)


class StrokesElement(Element):
    def __init__(self, master, **kwargs):
        super().__init__(master, 'Keystrokes per minute', '0', '0', **kwargs)


class AccuracyElement(Element):
    def __init__(self, master, **kwargs):
        super().__init__(master, 'Accuracy', '0', '0', **kwargs)


class StatsWidget(tm.TrainingMachineObserver, ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)

        self._ctx = None

        self._after_id = None
        self._pause_history = list()

        self._time_elem = TimeElement(self)
        self._strokes_elem = StrokesElement(self)
        self._accuracy_elem = AccuracyElement(self)
        self._progressbar = ttk.Progressbar(self, orient='horizontal', mode='determinate', value=0)

        self._time_elem.grid(column=0, row=0, sticky=N + S + W + E)
        self._strokes_elem.grid(column=1, row=0, sticky=N + S + W + E)
        self._accuracy_elem.grid(column=2, row=0, sticky=N + S + W + E)
        self._progressbar.grid(column=0, row=1, sticky=N + S + W + E, columnspan=3)

        self.columnconfigure(0, weight=1, minsize=self._time_elem.text_width)
        self.columnconfigure(1, weight=1, minsize=self._strokes_elem.text_width)
        self.columnconfigure(2, weight=1, minsize=self._accuracy_elem.text_width)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def set_context(self, ctx):
        self._ctx = ctx
        tm.add_observer(ctx, self)

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

        elapsed_seconds = timedelta.total_seconds(self.elapsed())
        minutes, seconds = divmod(elapsed_seconds, 60)
        self._time_elem.main = '{minutes:02.0f}:{seconds:02.1f}'.format(minutes=minutes, seconds=seconds)

        self._strokes_elem.main = '{:.0f}'.format((tm.strokes(self._ctx) / elapsed_seconds) * 60)

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

        self._time_elem.main = ZERO
        self._strokes_elem.main = '0'
        self._accuracy_elem.main('0 %')
        self._progressbar.configure(value=0)

    def on_end(self, ctx):
        self.after_cancel(self._after_id)
        self._after_id = None

        self._accuracy_elem.main = '{:.1%}'.format(tm.hits(self._ctx) / tm.strokes(self._ctx))
        self._progressbar.configure(value=tm.progress(self._ctx) * 100)

    def on_hit(self, ctx, index, typed):
        self._accuracy_elem.main = '{:.1%}'.format(tm.hits(self._ctx) / tm.strokes(self._ctx))
        self._progressbar.configure(value=tm.progress(self._ctx) * 100)

    def on_miss(self, ctx, index, typed, expected):
        self._accuracy_elem.main = '{:.1%}'.format(tm.hits(self._ctx) / tm.strokes(self._ctx))
        self._progressbar.configure(value=tm.progress(self._ctx) * 100)

    def on_undo(self, ctx, index, expect):
        self._accuracy_elem.main = '{:.1%}'.format(tm.hits(self._ctx) / tm.strokes(self._ctx))
        self._progressbar.configure(value=tm.progress(self._ctx) * 100)
