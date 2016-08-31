import logging
from datetime import timedelta
from math import floor

from tkinter import font
from tkinter import *
from tkinter import ttk

from pytouch.trainingmachine import *

logger = logging.getLogger(__name__)

# MODIFIERS = ('Control', 'Mod1', 'Command', 'Alt', 'Mod2', 'Option', 'Shift', 'Mod3', 'Lock', 'Mod4', 'Extended', 'Mod5')

# CONTROL_KEYS = ('Cancel', 'BackSpace', 'Tab', 'Return', 'Shift_L', 'Control_L', 'Alt_L', 'Pause', 'Caps_Lock', 'Escape',
# 'Prior ', 'Next', 'End', 'Home', 'Left', 'Up', 'Right', 'Down', 'Print', 'Insert', 'Delete',
# 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'Num_Lock', 'Scroll_Lock')

FILTERED_KEYS = ('Cancel', 'Tab', 'Shift_L', 'Control_L', 'Alt_L', 'Pause', 'Caps_Lock',
                 'Prior', 'Next', 'End', 'Home', 'Left', 'Up', 'Right', 'Down', 'Print', 'Insert', 'Delete',
                 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'Num_Lock', 'Scroll_Lock')

ZERO = '00:00.0'


class StatsElement(ttk.Frame):
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


class PauseDialog(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.lb_title = ttk.Label(self, text='Lesson paused')

        self.bt_continue = ttk.Button(self, text='Continue', default='active', command=self.on_continue)
        self.bt_restart = ttk.Button(self, text='Restart')
        self.bt_abort = ttk.Button(self, text='Abort')

        self.lb_title.grid(column=0, row=0)
        self.bt_continue.grid(column=0, row=1)
        self.bt_restart.grid(column=0, row=2)
        self.bt_abort.grid(column=0, row=3)

    def on_continue(self):
        logger.debug('on_continue')
        self.destroy()


class TrainingWidget(TrainingMachineObserver, Text):
    def __init__(self, master):
        super(TrainingWidget, self).__init__(master)

        self.tm = None
        self._after_id = None

        # text and scrollbar widget
        self._font = font.Font(family='mono', size=-40)

        self._text_frame = Frame(self)
        self._text = Text(self._text_frame, wrap=NONE, exportselection=0, undo=False)
        self._scrollbar = ttk.Scrollbar(self._text_frame, command=self._text.yview)
        # Connect scrollbar and training widget
        self._text['yscrollcommand'] = self._scrollbar.set

        # text tags
        self._text.tag_config('base', font=self._font, spacing1=20, justify=CENTER)
        self._text.tag_config('untyped', foreground='#cccccc')
        self._text.tag_config('hit')
        self._text.tag_config('miss', foreground='#cc0003')
        # text bindings
        self._text.bind('<Configure>', self.on_configure)
        self._text.bind('<FocusOut>', self.on_focus_out)
        self._text.bind('<KeyPress-Escape>', self.on_escape_press)
        self._text.bind('<KeyPress-BackSpace>', self.on_backspace_press)
        self._text.bind('<KeyPress>', self.on_key_press)
        self._text.bind('<Any-Button>', self.on_button)
        self._text.bind('<Motion>', lambda e: 'break')

        # statistics widgets
        self._time_elem = StatsElement(self, 'Elapsed time', ZERO, ZERO)
        self._strokes_elem = StatsElement(self, 'Keystrokes per minute', '0', '0')
        self._accuracy_elem = StatsElement(self, 'Accuracy', '0', '0')
        self._progressbar = ttk.Progressbar(self, orient='horizontal', mode='determinate', value=0)

        # pack and configure master frame
        self._time_elem.grid(column=0, row=0, sticky=N + S + W + E)
        self._strokes_elem.grid(column=1, row=0, sticky=N + S + W + E)
        self._accuracy_elem.grid(column=2, row=0, sticky=N + S + W + E)
        self._progressbar.grid(column=0, row=1, sticky=N + S + W + E, columnspan=3)
        self._text_frame.grid(column=0, row=2, sticky=N + S + W + E, columnspan=3)

        self.columnconfigure(0, weight=1, minsize=self._time_elem.text_width)
        self.columnconfigure(1, weight=1, minsize=self._strokes_elem.text_width)
        self.columnconfigure(2, weight=1, minsize=self._accuracy_elem.text_width)
        self.rowconfigure(2, weight=1)

        # pack and configure text frame
        self._text.grid(column=0, row=0, sticky=N + E + S + W)
        self._scrollbar.grid(column=1, row=0, sticky=N + E + S + W)

        self._text_frame.columnconfigure(0, weight=1, minsize=400)
        self._text_frame.rowconfigure(0, weight=1)

    def load_lesson(self, lesson):
        self.tm = TrainingMachine.from_lesson(lesson, auto_unpause=True)
        self.tm.add_observer(self)

        self._text.insert(index='1.0', chars=lesson.text)

        self._text.mark_set(INSERT, '1.0')

        self._text.tag_add('base', '1.0', '{}.end'.format(lesson.line_count))
        self._text.tag_add('untyped', '1.0', '{}.end'.format(lesson.line_count))

        # TODO: Use .tag_bind() to bind event to specific char. This is quite convenient. Qt should have a look at it :D
        # TODO: Use .see(index) to scroll to text out of scope. But how to center? .scan_mark(x, y)?
        # self.text_widget.tag_bind('untyped')  # Use it to bind event

        self._text.focus_set()
        self.update_font_size(self._text.cget('width'))

        return self.tm

    @property
    def idx(self):
        chars = self._text.count('1.0', INSERT, 'chars')
        return chars[0] if chars else 0

    def replace_char(self, index, char, tags):
        """ Replace a char at the given text index. """
        self._text.replace('1.0+{}c'.format(index), '1.0+{}c'.format(index + 1), char, tags)

    def update_font_size(self, width):
        # It seems to be impossible to determine the width of the cursor therefore the 25 pixels extra width.
        scale_factor = width / (self._font.measure(self.tm.lesson.longest_line) + 25)
        new_font_size = min(floor(self._font.cget('size') * scale_factor), -1)

        if self._font.cget('size') != new_font_size:
            logger.debug('Updating font size: {} -> {}'.format(self._font.cget('size'), new_font_size))

            self._font.configure(size=new_font_size)
            self._text.tag_config('base', spacing1=-new_font_size / 2)

    def on_configure(self, event):
        if event.width != self.cget('width'):
            logger.debug('update width {} -> {}'.format(self.cget('width'), event.width))
            pad = event.width * 0.03
            width = event.width - 2 * pad

            self.update_font_size(width)
            self._text.configure(padx=pad, pady=pad)

    def on_button(self, event):
        """ On any mouse button handler.
        Ignore all but set focus. This also disables any possibility to select text by mouse.
        """
        self._text.focus_set()
        return 'break'

    def on_focus_out(self, event):
        """ Pause TrainingMachine on focus out event. """
        self.tm.process_event(Event.pause_event())
        pass

    def on_escape_press(self, event):
        """ Pause and show dialog on ESC. """
        self.tm.process_event(Event.pause_event())
        # TODO: Show dialog
        print('SHOW DIALOG')
        return 'break'

    def on_backspace_press(self, event):
        """ Produce an undo TrainingMachine event on BackSpace. """
        if self.tm.paused:
            self.tm.process_event(Event.unpause_event())
        self.tm.process_event(Event.undo_event(self.idx))

        self._text.see(INSERT)
        return 'break'

    def on_key_press(self, event):
        """ Catch all key events. """

        # Note: For some reason Tk produces a CR (\r) as char for the Return event.
        # Nevertheless, Text expects NL (\n) for a new line when set programmatically.
        # FYI: Already tried to adjust the input channel configuration.
        if event.keysym == 'Return':
            event.char = '\n'

        # if tm.paused(self.tm):
        #     tm.process_event(self.tm, tm.Event.unpause_event())
        if event.char and event.keysym not in FILTERED_KEYS:
            self.tm.process_event(Event.input_event(self.idx, event.char))

        self._text.see(INSERT)
        return 'break'

    def _on_tick(self):
        self._after_id = self.after(100, self._on_tick)

        elapsed_seconds = timedelta.total_seconds(self.tm.elapsed())
        minutes, seconds = divmod(elapsed_seconds, 60)
        self._time_elem.main = '{minutes:02.0f}:{seconds:02.1f}'.format(minutes=minutes, seconds=seconds)

        self._strokes_elem.main = '{:.0f}'.format((self.tm.keystrokes / elapsed_seconds) * 60)

    def on_hit(self, sender, index, typed):
        """ TrainingMachine hit handler. """
        logger.debug('on_hit: insert {!r} at {}'.format(typed, index))
        self.replace_char(index, typed, ('base', 'hit'))

        self._accuracy_elem.main = '{:.1%}'.format(self.tm.hits / self.tm.keystrokes)
        self._progressbar.configure(value=self.tm.progress * 100)

    def on_miss(self, sender, index, typed, expected):
        """ TrainingMachine miss handler. """
        if typed != '<UNDO>':
            if typed != '\n':  # Do not output wrong linefeeds
                logger.debug('on_miss: typed {!r} expected {!r} at {}'.format(typed, expected, index))
                self.replace_char(index, typed, ('base', 'miss'))
        else:
            # TODO: Consequences?
            logger.debug('on_miss: typed {!r} expected {!r} at {}'.format(typed, expected, index))
            print('UNDO MISS')

        self._accuracy_elem.main = '{:.1%}'.format(self.tm.hits / self.tm.keystrokes)
        self._progressbar.configure(value=self.tm.progress * 100)

    def on_undo(self, sender, index, expect):
        """ TrainingMachine undo handler. """
        logger.debug('on_undo: undo at {} expecting {!r}'.format(index, expect))
        self.replace_char(index, expect, ('base', 'untyped'))
        self._text.mark_set(INSERT, '1.0+{}c'.format(index))

        self._accuracy_elem.main = '{:.1%}'.format(self.tm.hits / self.tm.keystrokes)
        self._progressbar.configure(value=self.tm.progress * 100)

    def on_pause(self, sender):
        """ TrainingMachine pause handler. """
        logger.debug('on_pause: ...')

        if self._after_id is None:
            logger.warning('Timer not running')
            return
        self.after_cancel(self._after_id)
        self._after_id = None

    def on_unpause(self, sender):
        """ TrainingMachine unpause handler. """
        logger.debug('on_unpause: ...')

        if self._after_id is not None:
            logger.warning('Timer already running')
            return
        self._after_id = self.after(100, self._on_tick)

    def on_restart(self, sender):
        """ TrainingMachine restart handler. """
        logger.debug('on_restart: ...')

        self.after_cancel(self._after_id)
        self._after_id = None

        self._time_elem.main = ZERO
        self._strokes_elem.main = '0'
        self._accuracy_elem.main('0 %')
        self._progressbar.configure(value=0)

    def on_end(self, sender):
        """ TrainingMachine end handler. """
        logger.debug('on_end: End reached')

        self.after_cancel(self._after_id)
        self._after_id = None

        self._accuracy_elem.main = '{:.1%}'.format(self.tm.hits / self.tm.keystrokes)
        self._progressbar.configure(value=self.tm.progress * 100)

        # def show_pause_dialog(self):
        # TODO: Build your own ttk PauseDialog grid it into all columns and rows and lift it above all other widgets.
        # Do not touch the weight of the PauseDialog to center it. Maybe it is possible to make the background
        # of the cell transparent??
