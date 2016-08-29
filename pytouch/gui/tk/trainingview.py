import logging

from tkinter import *
from tkinter import ttk

from pytouch.gui.tk.statswidget import StatsWidget
from pytouch.gui.tk.trainingwidget import TrainingWidget


class TrainingView(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.stats_widget = StatsWidget(self)
        self.training_widget = TrainingWidget(self)
        self.scrollbar = ttk.Scrollbar(self, command=self.training_widget.yview)

        # Connect scrollbar and training widget
        self.training_widget['yscrollcommand'] = self.scrollbar.set

        self.stats_widget.grid(column=0, row=0, columnspan=2, sticky=N + E + S + W)
        self.training_widget.grid(column=0, row=1, sticky=N + E + S + W)
        self.scrollbar.grid(column=1, row=1, sticky=N + E + S + W)

        self.columnconfigure(0, weight=1, minsize=400)
        self.rowconfigure(0, minsize=30)
        self.rowconfigure(1, weight=1)

        self.ctx = None

    def show(self, lesson):
        self.ctx = self.training_widget.load_lesson(lesson)
        self.stats_widget.set_context(self.ctx)
