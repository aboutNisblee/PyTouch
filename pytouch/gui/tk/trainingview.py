import logging

from tkinter import *
from tkinter import ttk

from pytouch.gui.tk.statswidget import StatsWidget
from pytouch.gui.tk.trainingwidget import TrainingWidget

import pytouch.trainingmachine as tm


class TrainingView(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, minsize=30)
        self.rowconfigure(1, weight=1)

        self.stats_widget = StatsWidget(self)
        self.stats_widget.grid(column=0, row=0, sticky=N + E + S + W)

        self.training_widget = TrainingWidget(self)
        # Training widget takes as much space as possible
        self.training_widget.grid(column=0, row=1, sticky=N + E + S + W)

        self.sb = ttk.Scrollbar(self, command=self.training_widget.yview)
        self.training_widget['yscrollcommand'] = self.sb.set
        # Add widgets to grid
        self.sb.grid(column=1, row=1, sticky=N + E + S + W)

        self.ctx = None

    def show(self, lesson):
        self.ctx = self.training_widget.load_lesson(lesson)
        tm.add_observer(self.ctx, self.stats_widget)

