import logging

from tkinter import *
from tkinter import ttk

from pytouch.service import CourseService
from pytouch.gui.tk.trainingwidget import TrainingWidget

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

        top.wm_title('PyTouch Typing Tutor')
        top.wm_iconname('PyTouch')
        # TODO: Add icon image
        # top.wm_iconphoto()

        self.training_widget = TrainingWidget(self)
        self.training_widget.grid(column=0, row=0, sticky=N + E + S + W)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')

    def show(self):
        self.training_widget.load_lesson(CourseService.find_lesson('{d6e5a9a9-3c31-4175-8d58-245695c60b08}'))

        self.master.update()
        self.master.minsize(self.master.winfo_width(), self.master.winfo_height())

        self.master.mainloop()
