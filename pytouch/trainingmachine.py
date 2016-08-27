import logging
import datetime

__all__ = [
    'Event',
    'TrainingMachineObserver',
    'TrainingContext',
    'add_observer',
    'remove_observer',
    'process_event',
    'is_paused',
    'is_running',
    'runtime',
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

    def on_pause(self, ctx):
        raise NotImplementedError

    def on_unpause(self, ctx):
        raise NotImplementedError

    def on_hit(self, ctx, index, typed):
        raise NotImplementedError

    def on_miss(self, ctx, index, typed, expected):
        raise NotImplementedError

    def on_undo(self, ctx, index, expect):
        """ Called after a successful undo event.
        :param ctx: The context.
        :param index: The index that should be replaced by the expect argument.
        :param expect: The expected character.
        """
        raise NotImplementedError

    def on_end(self, ctx):
        raise NotImplementedError

    def on_restart(self, ctx):
        raise NotImplementedError


class Char(object):
    def __init__(self, idx, char, undo_typo):
        self._idx = idx
        self._char = char
        self._input = list()
        self._undo_typo = undo_typo

    @property
    def index(self):
        return self._idx

    @property
    def char(self):
        return self._char

    @property
    def hit(self):
        return self._input[-1][0] == self._char if self._input else False

    @property
    def miss(self):
        return not self.hit

    @property
    def input(self):
        return self._input

    @property
    def typos(self):
        return [i for i in self._input if (i[0] != '<UNDO>' and i[0] != self._char) or (i[0] == '<UNDO>' and self._undo_typo)]

    def append(self, char, time=None):
        time = datetime.datetime.utcnow() if time is None else time
        self._input.append((char, time))

    def __getitem__(self, item):
        return self._input[item][0]

    def __iter__(self):
        for input in self._input:
            yield input


class TrainingContext(object):
    def __init__(self, text, undo_typo=False, **kwargs):
        """ Training machine context.

        A client should never manipulate internal attributes on its instance.

        Additional kwargs are added to the instance dict and can later be accessed as attributes.

        :param text: The lesson text.
        :param undo_typo: If enabled wrong undos count as typos.
        """

        # Ensure the text ends with NL
        if not text.endswith('\n'):
            text += '\n'

        self._state_fn = _state_pause
        self._text = [Char(i, c, undo_typo) for i, c in enumerate(text)]
        self._pause = list()
        self._observers = []
        self.undo_typo = undo_typo

        self.__dict__.update(kwargs)

    @classmethod
    def from_lesson(cls, lesson, **kwargs):
        """ Create a :class:`TrainingContext` from the given :class:`Lesson`.

        Additional arguments are passed to the context. The lesson is appended to the context.

        :param lesson: A :class:`Lesson`.
        :return: An instance of :class:`TrainingContext`.
        """
        return cls(lesson.text, lesson=lesson, **kwargs)

    def __getitem__(self, idx):
        return self._text[idx]

    def __iter__(self):
        for char in self._text:
            yield char


def add_observer(ctx, observer):
    """ Add an observer to the given context.

    :param ctx: A context.
    :param observer: An object implementing the :class:`TrainingMachineObserver` interface.
    """
    if observer not in ctx._observers:
        ctx._observers.append(observer)


def remove_observer(ctx, observer):
    """ Remove an observer from the given context.

    :param ctx: A context.
    :param observer: An object implementing the :class:`TrainingMachineObserver` interface.
    """
    ctx._observers.remove(observer)


def process_event(ctx, event):
    """ Process external event.

    :param ctx: A :class:`TrainingContext`.
    :param event: An event.
    """
    logger.debug('processing event: {}'.format(event))
    ctx._state_fn(ctx, event)


def is_paused(ctx):
    return ctx._state_fn is _state_pause


def is_running(ctx):
    return not is_paused(ctx) and ctx._state_fn is not _state_end


def _inputs(ctx):
    for char in ctx:
        for input in char:
            yield input


def runtime(ctx):
    """ Get the overall runtime.

    Only ended pauses are subtracted from the overall input time.

    :param ctx: A :class:`TrainingContext`
    :return: The runtime as :class:`datetime.timedelta`
    """

    # Sort all inputs by input time
    inputs = sorted(_inputs(ctx), key=lambda char: char[1])
    if not inputs:
        return datetime.timedelta(0)
    overall = inputs[-1][1] - inputs[0][1]
    # Subtract the sum of all ended pauses
    pause = sum((p[1] - p[0] for p in ctx._pause if p[1]), datetime.timedelta(0))
    rv = overall - pause
    logger.debug('runtime: overall {} pause {} runtime {}'.format(overall, pause, rv))
    return rv


def _notify(ctx, method, *args, **kwargs):
    for observer in ctx._observers:
        getattr(observer, method)(ctx, *args, **kwargs)


def _reset(ctx):
    ctx._state_fn = _state_pause
    for char in ctx:
        char.input.clear()


def _state_input(ctx, event):
    if event.type == 'pause':
        ctx._state_fn = _state_pause
        ctx._pause.append((datetime.datetime.utcnow(), None))
        _notify(ctx, 'on_pause')

    elif event.type == 'undo':
        if event.index > 0:
            ctx[event.index - 1].append('<UNDO>')

            # report wrong undos if desired
            if ctx.undo_typo:
                _notify(ctx, 'on_miss', event.index - 1, '<UNDO>', ctx[event.index - 1].char)

            _notify(ctx, 'on_undo', event.index - 1, ctx[event.index - 1].char)

    elif event.type == 'input':
        # Note that this may produce an IndexError. Let it happen! It's a bug in the caller.
        if ctx[event.index].char == event.char:  # hit
            ctx[event.index].append(event.char)
            _notify(ctx, 'on_hit', event.index, event.char)

            if event.index == ctx[-1].index:
                ctx._state_fn = _state_end
                _notify(ctx, 'on_end')

        else:  # miss
            if ctx[event.index].char == '\n':  # misses at line ending
                return  # TODO: Make misses on line ending configurable

            if event.char == '\n':  # 'Return' hits in line
                # TODO: Make misses on wrong returns configurable
                return

            ctx[event.index].append(event.char)
            _notify(ctx, 'on_miss', event.index, event.char, ctx[event.index].char)


def _state_pause(ctx, event):
    if event.type == 'unpause':
        ctx._state_fn = _state_input
        # Check for logical error
        if ctx._pause:
            if ctx._pause[-1][1] is not None:
                logger.error('Unpause event without preceding pause event')
            else:
                ctx._pause[-1] = (ctx._pause[-1][0], datetime.datetime.utcnow())
        _notify(ctx, 'on_unpause')


def _state_end(ctx, event):
    if event.type == 'restart':
        _reset(ctx)
        _notify(ctx, 'on_restart')
