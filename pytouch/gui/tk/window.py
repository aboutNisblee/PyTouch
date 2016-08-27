import logging

from tkinter import *
from tkinter import ttk

from pytouch.service import CourseService
from pytouch.gui.tk.trainingview import TrainingView

logger = logging.getLogger(__name__)


class MainWindow(ttk.Frame):
    def __init__(self, master=Tk()):
        super(MainWindow, self).__init__(master)

        # Pack self to expand to root
        self.grid(sticky=N + E + S + W)
        # Expand main window cell inside root
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.configure(width=400, height=300)

        self.test_lesson = CourseService.find_lesson('{d6e5a9a9-3c31-4175-8d58-245695c60b08}')
        self.training_view = TrainingView(self)
        self.training_view.grid(column=0, row=0, sticky=N + E + S + W)

    def show(self):
        self.training_view.show(self.test_lesson)
        self.master.mainloop()
