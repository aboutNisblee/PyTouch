from math import floor

from tkinter import font
from tkinter import *
from tkinter.ttk import *

from pytouch.model import Course, Lesson
from pytouch.service import CourseService
from pytouch.trainingmachine import *


# TODO: Derive widget from Text!
class TrainingWidget(TrainingMachineObserver, Frame):
    def __init__(self, master):
        super(TrainingWidget, self).__init__(master)
        self.lesson = None
        self.ctx = None

        # TODO: Make space for controls
        self.columnconfigure(0, weight=1)

        self.rowconfigure(0, minsize=50)
        self.rowconfigure(1, weight=1)

        self.font = font.Font(family='mono', size=-40)

        self.tw = Text(self, wrap=NONE, exportselection=0, undo=False)
        # Tags
        self.tw.tag_config('base', font=self.font, spacing1=20, justify=CENTER)
        self.tw.tag_config('untyped', foreground='#cccccc')
        self.tw.tag_config('hit')
        self.tw.tag_config('miss', foreground='#cc0003')
        # Bindings
        self.tw.bind('<Configure>', self.on_tw_configure)
        self.tw.bind('<FocusOut>', self.on_focus_out)
        self.tw.bind('<Any-KeyPress>', self.on_key_press)
        self.tw.bind('<Any-Button>', self.on_button)
        self.tw.bind('<Motion>', lambda e: 'break')

        self.sb = Scrollbar(self, command=self.tw.yview)
        self.tw['yscrollcommand'] = self.sb.set

        # Add widgets to grid
        self.tw.grid(column=0, row=1, sticky=N + E + S + W)
        self.sb.grid(column=1, row=1, sticky=N + E + S + W)

    def load_lesson(self, lesson):
        self.lesson = lesson
        self.ctx = context_from_lesson(lesson)
        add_observer(self.ctx, self)

        self.tw.insert(index='1.0', chars=self.lesson.text)

        self.tw.focus_set()
        self.tw.mark_set(INSERT, '1.0')

        self.tw.tag_add('base', '1.0', '{}.end'.format(lesson.lines))
        self.tw.tag_add('untyped', '1.0', '{}.end'.format(lesson.lines))

        # TODO: Use .tag_bind() to bind event to specific char. This is quite convenient. Qt should have a look at it :D
        # TODO: Use .see(index) to scroll to text out of scope. But how to center? .scan_mark(x, y)?
        # self.text_widget.tag_bind('untyped')  # Use it to bind event

    def on_tw_configure(self, event):
        if not self.lesson:
            return

        # FIXME: This isn't correct but for the moment I cannot find any possiblity to to determine the max char width.
        font_size = floor((event.width / self.lesson.max_chars) * 1.5)
        self.font.configure(size=-font_size)
        self.tw.tag_config('base', spacing1=font_size / 2)

    def on_button(self, event):
        self.tw.focus_set()
        return 'break'

    def on_focus_out(self, event):
        # TODO: PAUSE GAME
        process_event(self.ctx, Event.pause_event())
        print('PAUSE')

    def on_key_press(self, event):
        process_event(self.ctx, Event.input_event(event.char))
        return 'break'

    def on_hit(self, ctx, pos, char):
        self.tw.replace(INSERT, 'insert+1c', char, ('base', 'hit'))

    def on_miss(self, ctx, pos, char):
        self.tw.replace(INSERT, 'insert+1c', char, ('base', 'miss'))

    def on_undo(self, ctx):
        pass

    def on_pause(self, ctx):
        pass

    def on_unpause(self, ctx):
        pass

    def on_restart(self, ctx):
        pass

    def on_finish(self, ctx):
        pass


class MainWindow(Frame):
    def __init__(self, master=Tk()):
        super(MainWindow, self).__init__(master)

        # Pack self to expand to root
        self.grid(sticky=N + E + S + W)
        # Expand main window cell inside root
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, minsize=30)
        self.rowconfigure(0, weight=1)

        self.training_widget = TrainingWidget(self)
        # Training widget takes as much space as possible
        self.training_widget.grid(column=0, row=0, sticky=N + E + S + W)

        self.training_widget.load_lesson(CourseService.find_lesson('{3de91ad7-0c6a-4b38-bbb3-2a8007eb7696}'))

    def show(self):
        self.master.mainloop()
