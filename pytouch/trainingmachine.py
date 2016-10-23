import copy
import logging
from datetime import datetime, timedelta

from collections import namedtuple

from blinker import Signal

__all__ = [
    'Event',
    'TrainingMachineObserver',
    'TrainingMachine',
]

logger = logging.getLogger(__name__)


class Event(dict):
    """ Events that are expected by the process_event function.
    Use the factory methods to create appropriate events.
    """

    def __init__(self, type, **kwargs):
        super().__init__(type=type, **kwargs)

    @property
    def type(self):
        return self['type']

    @property
    def index(self):
        return self.get('index')

    @property
    def char(self):
        return self.get('char')

    @classmethod
    def input_event(cls, index, char):
        return cls(type='input', index=index, char=char)

    @classmethod
    def undo_event(cls, index):
        """ Create an undo event.
        :param index: The index right of the char that should be reverted.
        """
        return cls(type='undo', index=index)

    @classmethod
    def pause_event(cls):
        return cls(type='pause')

    @classmethod
    def unpause_event(cls):
        return cls(type='unpause')

    @classmethod
    def restart_event(cls):
        return cls(type='restart')


class TrainingMachineObserver(object):
    """ TrainingMachine observer interface.

    A client should implement this interface to get feedback from the machine.
    """

    def on_pause(self, sender):
        raise NotImplementedError

    def on_unpause(self, sender):
        raise NotImplementedError

    def on_hit(self, sender, index, typed):
        raise NotImplementedError

    def on_miss(self, sender, index, typed, expected):
        raise NotImplementedError

    def on_undo(self, sender, index, expect):
        """ Called after a successful undo event.
        :param sender: The sending machine.
        :param index: The index that should be replaced by the expect argument.
        :param expect: The expected character.
        """
        raise NotImplementedError

    def on_end(self, sender):
        raise NotImplementedError

    def on_restart(self, sender):
        raise NotImplementedError


class Char(object):
    KeyStroke = namedtuple('KeyStroke', ['char', 'time'])

    def __init__(self, idx, char, undo_typo):
        """ Internal representation of a character in the text of a lesson.

        An additional list of all key strokes at this index is maintained.


        :param idx: The absolute index in the text starting at 0.
        :param char: The utf-8 character in the text.
        :param undo_typo: Should undos (<UNDO>) counts as typos.
        """
        self._idx = idx
        self._char = char
        self._keystrokes = list()
        self._undo_typo = undo_typo

    @property
    def index(self):
        return self._idx

    @property
    def char(self):
        return self._char

    @property
    def hit(self):
        """ Is the last recorded key stroke a hit?
        :return: True on hit, else False.
        """
        return self._keystrokes[-1].char == self._char if self._keystrokes else False

    @property
    def miss(self):
        """ Is the last recorded key stroke a miss?
        :return: True on miss, else False.
        """
        return not self.hit

    @property
    def keystrokes(self):
        return self._keystrokes

    @property
    def typos(self):
        return [ks for ks in self._keystrokes if (ks.char != '<UNDO>' and ks.char != self._char) or (ks.char == '<UNDO>' and self._undo_typo)]

    def append(self, char, elapsed):
        self._keystrokes.append(Char.KeyStroke(char, elapsed))

    def __getitem__(self, item):
        return self._keystrokes[item].char

    def __iter__(self):
        for ks in self._keystrokes:
            yield ks


class TrainingMachine(object):
    PauseEntry = namedtuple('PauseEntry', ['action', 'time'])

    def __init__(self, text, auto_unpause=False, undo_typo=False, **kwargs):
        """ Training machine.

        A client should never manipulate internal attributes on its instance.

        Additional kwargs are added to the instance dict and can later be accessed as attributes.

        Note that the logic is currently initialized with paused state. In case auto_unpause is False
        the logic must first be unpaused by passing an unpause event to start the state machine.
        If auto_unpause is True, the machine automatically switches state to input on first input event.
        In either case an on_unpause callback is made that the gui can use to detect the start of the training
        session.

        :param text: The lesson text.
        :param undo_typo: If enabled wrong undos count as typos.
        :param auto_unpause: True to enable the auto transition from pause to input on input event.
        """

        # Ensure the text ends with NL
        if not text.endswith('\n'):
            text += '\n'

        self._state_fn = self._state_pause
        self._text = [Char(i, c, undo_typo) for i, c in enumerate(text)]
        self._pause_history = list()
        self._observers = list()

        self.auto_unpause = auto_unpause
        self.undo_typo = undo_typo

        self.__dict__.update(kwargs)

    @classmethod
    def from_lesson(cls, lesson, **kwargs):
        """ Create a :class:`TrainingMachine` from the given :class:`Lesson`.

        Additional arguments are passed to the context. The lesson is appended to the context.

        :param lesson: A :class:`Lesson`.
        :return: An instance of :class:`TrainingMachine`.
        """
        return cls(lesson.text, lesson=lesson, **kwargs)

    def add_observer(self, observer):
        """ Add an observer to the given machine.

        :param observer: An object implementing the :class:`TrainingMachineObserver` interface.
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """ Remove an observer from the given machine.

        :param observer: An object implementing the :class:`TrainingMachineObserver` interface.
        """
        self._observers.remove(observer)

    def process_event(self, event):
        """ Process external event.

        :param event: An event.
        """
        logger.debug('processing event: {}'.format(event))
        self._state_fn(event)

    @property
    def paused(self):
        return self._state_fn is self._state_pause

    @property
    def running(self):
        return not self.paused and self._state_fn is not self._state_end

    def _keystrokes(self):
        for char in self._text:
            for ks in char:
                yield ks

    @property
    def keystrokes(self):
        return len([ks for ks in self._keystrokes() if ks.char != '<UNDO>'])

    @property
    def hits(self):
        return len([char for char in self._text if char.hit])

    @property
    def progress(self):
        rv = self.hits / len(self._text)
        return rv

    def elapsed(self):
        """ Get the overall runtime.

        :return: The runtime as :class:`datetime.timedelta`
        """

        if not self._pause_history:
            return timedelta(0)

        # Sort all inputs by input time
        # keystrokes = sorted(self._keystrokes(), key=lambda ks: ks.time)

        overall = datetime.utcnow() - self._pause_history[0].time

        pause_time = timedelta(0)

        # make a deep copy of the pause history
        history = copy.deepcopy(self._pause_history)
        # pop last event if we are still running or just started
        if history[-1].action in ['start', 'unpause']:
            history.pop()

        def pairs(iterable):
            it = iter(iterable)
            return zip(it, it)

        for start, stop in pairs(history):
            pause_time += (stop.time - start.time)

        return overall - pause_time

    def _notify(self, method, *args, **kwargs):
        for observer in self._observers:
            getattr(observer, method)(self, *args, **kwargs)

    def _reset(self):
        self._state_fn = self._state_pause
        for char in self._text:
            char.keystrokes.clear()

    def _state_input(self, event):
        if event.type == 'pause':
            self._state_fn = self._state_pause
            self._pause_history.append(TrainingMachine.PauseEntry('pause', datetime.utcnow()))
            self._notify('on_pause')

        elif event.type == 'undo':
            if event.index > 0:
                self._text[event.index - 1].append('<UNDO>', self.elapsed())

                # report wrong undos if desired
                if self.undo_typo:
                    self._notify('on_miss', event.index - 1, '<UNDO>', self._text[event.index - 1].char)

                self._notify('on_undo', event.index - 1, self._text[event.index - 1].char)

        elif event.type == 'input':
            # Note that this may produce an IndexError. Let it happen! It's a bug in the caller.
            if self._text[event.index].char == event.char:  # hit
                self._text[event.index].append(event.char, self.elapsed())
                self._notify('on_hit', event.index, event.char)

                if event.index == self._text[-1].index:
                    self._state_fn = self._state_end
                    self._pause_history.append(TrainingMachine.PauseEntry('stop', datetime.utcnow()))
                    self._notify('on_end')

            else:  # miss
                if self._text[event.index].char == '\n':  # misses at line ending
                    return  # TODO: Make misses on line ending configurable

                if event.char == '\n':  # 'Return' hits in line
                    # TODO: Make misses on wrong returns configurable
                    return

                self._text[event.index].append(event.char, self.elapsed())
                self._notify('on_miss', event.index, event.char, self._text[event.index].char)

    def _state_pause(self, event):
        if event.type == 'unpause' or (event.type == 'input' and self.auto_unpause):
            self._state_fn = self._state_input
            if self._pause_history:
                # Only append start time if we've already had a pause event.
                # Currently we're detecting the start view first keystroke time.
                self._pause_history.append(TrainingMachine.PauseEntry('unpause', datetime.utcnow()))
            else:
                self._pause_history.append(TrainingMachine.PauseEntry('start', datetime.utcnow()))
            self._notify('on_unpause')
            if event.type == 'input' and self.auto_unpause:
                # Auto transition to input state
                self._state_input(event)

    def _state_end(self, event):
        if event.type == 'restart':
            self._reset()
            self._notify('on_restart')
