import logging
from functools import partial
from math import floor

from tkinter import font
from tkinter import *
from tkinter import ttk

from pytouch.model import Course, Lesson
from pytouch.service import CourseService
import pytouch.trainingmachine as tm

logger = logging.getLogger(__name__)

# MODIFIERS = ('Control', 'Mod1', 'Command', 'Alt', 'Mod2', 'Option', 'Shift', 'Mod3', 'Lock', 'Mod4', 'Extended', 'Mod5')

# CONTROL_KEYS = ('Cancel', 'BackSpace', 'Tab', 'Return', 'Shift_L', 'Control_L', 'Alt_L', 'Pause', 'Caps_Lock', 'Escape',
# 'Prior ', 'Next', 'End', 'Home', 'Left', 'Up', 'Right', 'Down', 'Print', 'Insert', 'Delete',
# 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'Num_Lock', 'Scroll_Lock')

FILTERED_KEYS = ('Cancel', 'Tab', 'Shift_L', 'Control_L', 'Alt_L', 'Pause', 'Caps_Lock',
                 'Prior', 'Next', 'End', 'Home', 'Left', 'Up', 'Right', 'Down', 'Print', 'Insert', 'Delete',
                 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'Num_Lock', 'Scroll_Lock')


# Undo: 'BackSpace'
# Pause: 'Escape'
# Linefeed: 'Return'

class TrainingWidget(tm.TrainingMachineObserver, Text):
    def __init__(self, master, lesson):
        super(TrainingWidget, self).__init__(master, wrap=NONE, exportselection=0, undo=False)

        self.lesson = lesson
        self.ctx = None

        self.font = font.Font(family='mono', size=-40)

        # Tags
        self.tag_config('base', font=self.font, spacing1=20, justify=CENTER)
        self.tag_config('untyped', foreground='#cccccc')
        self.tag_config('hit')
        self.tag_config('miss', foreground='#cc0003')
        # Bindings
        self.bind('<Configure>', self.on_configure)
        self.bind('<FocusOut>', self.on_focus_out)
        self.bind('<KeyPress-Escape>', self.on_escape_press)
        self.bind('<KeyPress-BackSpace>', self.on_backspace_press)
        self.bind('<KeyPress>', self.on_key_press)
        self.bind('<Any-Button>', self.on_button)
        self.bind('<Motion>', lambda e: 'break')

        self.load_lesson(self.lesson)

        # TODO: Move me to containing view
        # self.sb = Scrollbar(self, command=self.yview)
        # self['yscrollcommand'] = self.sb.set
        # Add widgets to grid
        # self.grid(column=0, row=1, sticky=N + E + S + W)
        # self.sb.grid(column=1, row=1, sticky=N + E + S + W)

    def load_lesson(self, lesson):
        self.ctx = tm.context_from_lesson(lesson, enforced_correction=False)
        tm.add_observer(self.ctx, self)

        self.insert(index='1.0', chars=lesson.text)

        self.mark_set(INSERT, '1.0')

        self.tag_add('base', '1.0', '{}.end'.format(lesson.line_count))
        self.tag_add('untyped', '1.0', '{}.end'.format(lesson.line_count))

        # TODO: Use .tag_bind() to bind event to specific char. This is quite convenient. Qt should have a look at it :D
        # TODO: Use .see(index) to scroll to text out of scope. But how to center? .scan_mark(x, y)?
        # self.text_widget.tag_bind('untyped')  # Use it to bind event

        self.focus_set()
        self.update_font_size(self.cget('width'))

    def replace_char(self, index, char, tags):
        """ Replace a char at the given text index. """
        self.replace('1.0+{}c'.format(index), '1.0+{}c'.format(index + 1), char, tags)

    def update_font_size(self, width):
        # It seems to be impossible to determine the width of the cursor therefore the 25 pixels extra width.
        scale_factor = width / (self.font.measure(self.lesson.longest_line) + 25)
        new_font_size = min(floor(self.font.cget('size') * scale_factor), -1)

        if self.font.cget('size') != new_font_size:
            logger.debug('Updating font size: {} -> {}'.format(self.font.cget('size'), new_font_size))

            self.font.configure(size=new_font_size)
            self.tag_config('base', spacing1=-new_font_size / 2)

    def on_configure(self, event):
        if event.width != self.cget('width'):
            logger.debug('update width {} -> {}'.format(self.cget('width'), event.width))
            pad = event.width * 0.03
            width = event.width - 2 * pad

            self.update_font_size(width)
            self.configure(padx=pad, pady=pad)

    def on_button(self, event):
        """ On any mouse button handler.
        Ignore all but set focus. This also disables any possibility to select text by mouse.
        """
        self.focus_set()
        return 'break'

    def on_focus_out(self, event):
        """ Pause TrainingMachine on focus out event. """
        tm.process_event(self.ctx, tm.Event.pause_event())

    def on_escape_press(self, event):
        """ Pause and show dialog on ESC. """
        tm.process_event(self.ctx, tm.Event.pause_event())
        # TODO: Show dialog
        print('SHOW DIALOG')
        return 'break'

    def on_backspace_press(self, event):
        """ Produce an undo TrainingMachine event on BackSpace. """
        if tm.is_paused(self.ctx):
            tm.process_event(self.ctx, tm.Event.unpause_event())
        tm.process_event(self.ctx, tm.Event.undo_event())
        self.see(INSERT)
        return 'break'

    def advance_allowed(self):
        # FIXME: CRAP!
        return not (self.ctx.enforced_correction and tm.is_miss(self.ctx))

    def insert2index(self):
        # TODO: It should be much easier to pass the current index into the machine than tracking
        # the index separately inside the machine!
        logging.debug(self.count('1.0', INSERT, 'chars'))

    def on_key_press(self, event):
        """ Catch all key events. """

        # Note: For some reason Tk produces a CR (\r) as char for the Return event.
        # Nevertheless, Text expects NL (\n) for a new line when set programmatically.
        # FYI: Already tried to adjust the input channel configuration.
        if event.keysym == 'Return':
            event.char = '\n'

        self.insert2index()

        if tm.is_paused(self.ctx):
            tm.process_event(self.ctx, tm.Event.unpause_event())
        if self.advance_allowed() and event.char and event.keysym not in FILTERED_KEYS:
            tm.process_event(self.ctx, tm.Event.input_event(event.char))
        self.see(INSERT)

        self.insert2index()

        return 'break'

    def on_hit(self, ctx, index, typed):
        """ TrainingMachine hit handler. """
        logger.debug('on_hit: insert {!r} at {}'.format(typed, index))
        # TODO: No need to replace! Changing the tags should be sufficient.
        self.replace_char(index, typed, ('base', 'hit'))

    def on_miss(self, ctx, index, typed, expected):
        """ TrainingMachine miss handler. """
        if typed != '<UNDO>':
            if typed != '\n':  # Do not output wrong linefeeds
                logger.debug('on_miss: typed {!r} expected {!r} at {}'.format(typed, expected, index))
                self.replace_char(index, typed, ('base', 'miss'))
        else:
            # TODO: Consequences?
            logger.debug('on_miss: typed {!r} expected {!r} at {}'.format(typed, expected, index))
            print('UNDO MISS')

    def on_undo(self, ctx, index, expect):
        """ TrainingMachine undo handler. """
        logger.debug('on_undo: undo at {} expecting {!r}'.format(index, expect))
        self.replace_char(index, expect, ('base', 'untyped'))
        self.mark_set(INSERT, '1.0+{}c'.format(index))

    def on_pause(self, ctx):
        """ TrainingMachine pause handler. """
        logger.debug('on_pause: ...')

    def on_unpause(self, ctx):
        """ TrainingMachine unpause handler. """
        logger.debug('on_unpause: ...')

    def on_restart(self, ctx):
        """ TrainingMachine restart handler. """
        logger.debug('on_restart: ...')

    def on_finish(self, ctx):
        """ TrainingMachine finish handler. """
        logger.debug('on_finish: Yeehaa!')
        self.configure(state='disabled')
