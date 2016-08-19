import logging

__all__ = [
    'Event',
    'TrainingMachineObserver',
    'TrainingContext',
    'add_observer',
    'remove_observer',
    'process_event',
    'context_from_lesson',
]


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
    def char(self):
        return self.get('char')

    @classmethod
    def input_event(cls, char):
        return cls(type='input', char=char)

    @classmethod
    def undo_event(cls):
        return cls(type='undo')

    @classmethod
    def pause_event(cls):
        return cls(type='pause')

    @classmethod
    def unpause_event(cls):
        return cls(type='unpause')

    @classmethod
    def exit_event(cls):
        return cls(type='exit')

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

    def on_hit(self, ctx, pos, char):
        raise NotImplementedError

    def on_miss(self, ctx, pos, char):
        raise NotImplementedError

    def on_undo(self, ctx):
        raise NotImplementedError

    def on_finish(self, ctx):
        raise NotImplementedError

    def on_restart(self, ctx):
        raise NotImplementedError


class TrainingContext(object):
    def __init__(self, text, linefeed_mode='normal', enforced_correction=False, undo_typo=False):
        """ Training machine context.

        A client should never manipulate internal attributes on its instance.

        :param text: The lesson text.
        :param linefeed_mode: 'normal': Return expected. 'space': Space expected. 'skip': Nothing expected.
        :param enforced_correction: If enabled corrections are enforced. (No further typing after typos)
        :param undo_typo: If enabled wrong undos count as typos.
        """
        self._state_fn = _state_input
        self._text = list(text)
        self._input = list()  # Only track all inputs
        self._typos = list()  # List of tuples of position and char
        self._pos = 0
        self._expect = self._text[self._pos] if self._text else None
        self._miss_flag = False  # Not nice

        self._observers = []

        self.linefeed_mode = linefeed_mode
        self.enforced_correction = enforced_correction
        self.undo_typo = undo_typo


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
    ctx._state_fn(ctx, event)


def context_from_lesson(lesson, *args, **kwargs):
    """ Create a :class:`TrainingContext` from the given :class:`Lesson`.

    Additional arguments are passed to the context.

    :param lesson: A :class:`Lesson`.
    :return: An instance of :class:`TrainingContext`.
    """
    return TrainingContext(lesson.text, *args, **kwargs)


def _notify(ctx, method, *args, **kwargs):
    for observer in ctx._observers:
        getattr(observer, method)(ctx, *args, **kwargs)


def _reset(ctx):
    ctx._state_fn = _state_input
    ctx._input = list()
    ctx._typos = list()
    ctx._pos = 0
    ctx._expect = ctx._text[ctx._pos] if ctx._text else None
    ctx._miss_flag = False


def _state_input(ctx, event):
    if event.type == 'pause':
        ctx._state_fn = _state_pause
        _notify(ctx, 'on_pause')

    elif event.type == 'undo':
        if ctx._pos > 0:
            ctx._input.append((ctx._pos, '<UNDO>'))

            # count wrong undos if desired
            if not ctx._miss_flag and ctx.undo_typo:
                ctx._typos.append((ctx._pos, '<UNDO>'))
                _notify(ctx, 'on_miss', ctx._pos, '<UNDO>')

            ctx._pos -= 1
            ctx._expect = ctx._text[ctx._pos]
            _notify(ctx, 'on_undo')

    elif event.type == 'input':
        # Record all inputs
        ctx._input.append((ctx._pos, event.char))

        if event.char == ctx._expect:  # hit
            ctx._miss_flag = False
            _notify(ctx, 'on_hit', ctx._pos, event.char)
            ctx._pos += 1
            try:
                ctx._expect = ctx._text[ctx._pos]
            except IndexError:
                # Finish!
                ctx._pos -= 1
                ctx._state_fn = _state_finish
                _notify(ctx, 'on_finish')

        else:  # miss
            ctx._miss_flag = True
            ctx._typos.append((ctx._pos, event.char))
            _notify(ctx, 'on_miss', ctx._pos, event.char)

            # If correction isn't enforced advance position
            # and expected char but skip win detection.
            if not ctx.enforced_correction:
                ctx._pos += 1
                try:
                    ctx._expect = ctx._text[ctx._pos]
                except IndexError:
                    ctx._pos -= 1


def _state_pause(ctx, event):
    if event.type == 'unpause':
        ctx._state_fn = _state_input
        _notify(ctx, 'on_unpause')


def _state_finish(ctx, event):
    if event.type == 'restart':
        _reset(ctx)
        _notify(ctx, 'on_restart')
