from unittest.mock import MagicMock, call

from nose.tools import eq_

from pytouch.trainingmachine import *
from pytouch.trainingmachine import _state_pause, _state_input, _state_finish

TEXT = 'f j\nf'


class TestTrainingMachine(object):
    def setup(self):
        self.feedback_mock = MagicMock()
        self.ctx = TrainingContext(TEXT)
        self.ctx.add_observer(self.feedback_mock)

    def test_pause(self):
        # pause and check inner state change
        process_event(self.ctx, Event.pause_event())
        eq_(self.ctx._state_fn, _state_pause)

        # unpause and check inner state change
        process_event(self.ctx, Event.unpause_event())
        eq_(self.ctx._state_fn, _state_input)

        # check feedback calls
        self.feedback_mock.assert_has_calls([call.pause(self.ctx), call.unpause(self.ctx)])

    def test_hit(self):
        process_event(self.ctx, Event.input_event(TEXT[0]))
        eq_(self.ctx._state_fn, _state_input)
        eq_(self.ctx._pos, 1)
        eq_(self.ctx._expect, TEXT[1])
        eq_(self.ctx._input, [(0, TEXT[0])])
        eq_(self.ctx._typos, [])
        self.feedback_mock.assert_has_calls([call.hit(self.ctx, 0, TEXT[0])])

    def test_miss_undo_not_enforced(self):
        self.ctx.enforced_correction = False
        process_event(self.ctx, Event.input_event(TEXT[1]))  # miss
        process_event(self.ctx, Event.input_event(TEXT[0]))  # miss
        eq_(self.ctx._pos, 2)
        eq_(self.ctx._expect, TEXT[2])
        eq_(self.ctx._input, [(0, TEXT[1]), (1, TEXT[0])])
        eq_(self.ctx._typos, [(0, TEXT[1]), (1, TEXT[0])])
        self.feedback_mock.assert_has_calls([call.miss(self.ctx, 0, TEXT[1]), call.miss(self.ctx, 1, TEXT[0])])

    def test_miss_undo_enforced(self):
        self.ctx.enforced_correction = True
        process_event(self.ctx, Event.input_event(TEXT[1]))  # miss
        process_event(self.ctx, Event.input_event(TEXT[1]))  # miss
        eq_(self.ctx._pos, 0)
        eq_(self.ctx._expect, TEXT[0])
        eq_(self.ctx._input, [(0, TEXT[1]), (0, TEXT[1])])
        eq_(self.ctx._typos, [(0, TEXT[1]), (0, TEXT[1])])
        self.feedback_mock.assert_has_calls([call.miss(self.ctx, 0, TEXT[1]), call.miss(self.ctx, 0, TEXT[1])])

    def test_undo_miss(self):
        process_event(self.ctx, Event.input_event(TEXT[0]))  # hit
        process_event(self.ctx, Event.input_event(TEXT[2]))  # miss
        process_event(self.ctx, Event.undo_event())
        eq_(self.ctx._pos, 1)
        eq_(self.ctx._expect, TEXT[1])
        eq_(self.ctx._input, [(0, TEXT[0]), (1, TEXT[2]), (2, '<UNDO>')])
        eq_(self.ctx._typos, [(1, TEXT[2])])
        self.feedback_mock.assert_has_calls([call.undo(self.ctx)])

    def test_undo_hit(self):
        process_event(self.ctx, Event.input_event(TEXT[0]))  # hit
        process_event(self.ctx, Event.undo_event())
        eq_(self.ctx._pos, 0)
        eq_(self.ctx._expect, TEXT[0])
        eq_(self.ctx._input, [(0, TEXT[0]), (1, '<UNDO>')])
        eq_(self.ctx._typos, [])
        self.feedback_mock.assert_has_calls([call.undo(self.ctx)])

    def test_undo_hit_undo_typo_enabled(self):
        self.ctx.undo_typo = True  # An undo of a hit should count as typo/miss
        process_event(self.ctx, Event.input_event(TEXT[0]))  # hit
        process_event(self.ctx, Event.undo_event())
        eq_(self.ctx._pos, 0)
        eq_(self.ctx._expect, TEXT[0])
        eq_(self.ctx._input, [(0, TEXT[0]), (1, '<UNDO>')])
        eq_(self.ctx._typos, [(1, '<UNDO>')])
        self.feedback_mock.assert_has_calls([call.miss(self.ctx, 1, '<UNDO>'), call.undo(self.ctx)])

    def test_undo_fail_at_start(self):
        process_event(self.ctx, Event.undo_event())
        eq_(self.ctx._pos, 0)
        eq_(self.ctx._expect, TEXT[0])
        eq_(self.ctx._input, [])
        eq_(self.ctx._typos, [])
        self.feedback_mock.assert_not_called()

    def test_finish(self):
        for char in TEXT:
            process_event(self.ctx, Event.input_event(char))
        eq_(self.ctx._state_fn, _state_finish)
        eq_(self.ctx._pos, len(TEXT) - 1)
        eq_(self.ctx._expect, TEXT[-1])
        eq_(self.ctx._input, list(enumerate(TEXT)))
        eq_(self.ctx._typos, [])
        self.feedback_mock.assert_has_calls([call.finish(self.ctx)])

# def test_space(self):
# def test_linefeed(self):
