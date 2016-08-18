import logging

__all__ = ['Event', 'FeedbackInterface', 'TrainingContext', 'process_event']


class Event(dict):
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


class FeedbackInterface(object):
    """ Feedback interface.

    A client should implement this interface to get feedback from the machine.
    """

    @staticmethod
    def pause(ctx):
        raise NotImplementedError

    @staticmethod
    def unpause(ctx):
        raise NotImplementedError

    @staticmethod
    def hit(ctx, pos, char):
        raise NotImplementedError

    @staticmethod
    def miss(ctx, pos, char):
        raise NotImplementedError

    @staticmethod
    def undo(ctx):
        raise NotImplementedError

    @staticmethod
    def finish(ctx):
        raise NotImplementedError

    @staticmethod
    def restart(ctx):
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
        self._expect = self._text[self._pos]
        self._miss_flag = False  # Not nice

        self._feedback_handlers = []

        self.linefeed_mode = linefeed_mode
        self.enforced_correction = enforced_correction
        self.undo_typo = undo_typo

    @classmethod
    def from_lesson(cls, lesson):
        return cls(lesson.text)

    def add_observer(self, feedback_handler):
        if feedback_handler not in self._feedback_handlers:
            self._feedback_handlers.append(feedback_handler)

    def remove_observer(self, feedback_handler):
        self._feedback_handlers.remove(feedback_handler)

    def _reset(self):
        self._state_fn = _state_input
        self._input = list()
        self._typos = list()
        self._pos = 0
        self._expect = self._text[self._pos]
        self._miss_flag = False


def _feedback(ctx, method, *args, **kwargs):
    for handler in ctx._feedback_handlers:
        getattr(handler, method)(ctx, *args, **kwargs)


def _state_input(ctx, event):
    if event.type == 'pause':
        ctx._state_fn = _state_pause
        _feedback(ctx, 'pause')

    elif event.type == 'undo':
        if ctx._pos > 0:
            ctx._input.append((ctx._pos, '<UNDO>'))

            # count wrong undos if desired
            if not ctx._miss_flag and ctx.undo_typo:
                ctx._typos.append((ctx._pos, '<UNDO>'))
                _feedback(ctx, 'miss', ctx._pos, '<UNDO>')

            ctx._pos -= 1
            ctx._expect = ctx._text[ctx._pos]
            _feedback(ctx, 'undo')

    elif event.type == 'input':
        # Record all inputs
        ctx._input.append((ctx._pos, event.char))

        if event.char == ctx._expect:  # hit
            ctx._miss_flag = False
            _feedback(ctx, 'hit', ctx._pos, event.char)
            ctx._pos += 1
            try:
                ctx._expect = ctx._text[ctx._pos]
            except IndexError:
                # Finish!
                ctx._pos -= 1
                ctx._state_fn = _state_finish
                _feedback(ctx, 'finish')

        else:  # miss
            ctx._miss_flag = True
            ctx._typos.append((ctx._pos, event.char))
            _feedback(ctx, 'miss', ctx._pos, event.char)

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
        _feedback(ctx, 'unpause')


def _state_finish(ctx, event):
    if event.type == 'restart':
        ctx._reset()
        _feedback(ctx, 'restart')


def process_event(ctx, event):
    """ Process external event.

    :param ctx: The machine context.
    :param event: The event.
    """
    ctx._state_fn(ctx, event)
