from unittest.mock import MagicMock, call

from nose.tools import eq_, assert_raises, assert_list_equal

from pytouch.trainingmachine import *
from pytouch.trainingmachine import _state_pause, _state_input, _state_end

TEXT = 'f j\nf'


def check_char_list(list, expect):
    if not list:
        eq_(list, expect)
    else:
        for i, char in enumerate(list):
            eq_(char[0], expect[i])


class TestTrainingMachine(object):
    def setup(self):
        self.feedback_mock = MagicMock()
        self.ctx = TrainingContext(TEXT)
        add_observer(self.ctx, self.feedback_mock)

    def test_init(self):
        for i, c in enumerate(TEXT + '\n'):
            eq_(self.ctx[i].index, i)
            eq_(self.ctx[i].char, c)
            eq_(self.ctx[i].hit, False)
            eq_(self.ctx[i].miss, True)
            check_char_list(self.ctx[i].input, [])
            check_char_list(self.ctx[i].typos, [])

    def test_pause(self):
        # pause and check inner state change
        process_event(self.ctx, Event.pause_event())
        eq_(self.ctx._state_fn, _state_pause)

        # unpause and check inner state change
        process_event(self.ctx, Event.unpause_event())
        eq_(self.ctx._state_fn, _state_input)

        # check feedback
        self.feedback_mock.assert_has_calls([call.on_pause(self.ctx), call.on_unpause(self.ctx)])

    def test_hit(self):
        process_event(self.ctx, Event.input_event(0, TEXT[0]))
        eq_(self.ctx._state_fn, _state_input)
        eq_(self.ctx[0].hit, True)
        eq_(self.ctx[0].miss, False)
        check_char_list(self.ctx[0].input, [TEXT[0]])
        check_char_list(self.ctx[0].typos, [])
        self.feedback_mock.assert_has_calls([call.on_hit(self.ctx, 0, TEXT[0])])

    def test_miss(self):
        process_event(self.ctx, Event.input_event(0, TEXT[1]))
        eq_(self.ctx._state_fn, _state_input)
        eq_(self.ctx[0].hit, False)
        eq_(self.ctx[0].miss, True)
        check_char_list(self.ctx[0].input, [TEXT[1]])
        check_char_list(self.ctx[0].typos, [TEXT[1]])
        self.feedback_mock.assert_has_calls([call.on_miss(self.ctx, 0, TEXT[1], TEXT[0])])

    def test_undo_miss(self):
        process_event(self.ctx, Event.input_event(0, TEXT[0]))  # hit
        process_event(self.ctx, Event.input_event(1, TEXT[2]))  # miss
        process_event(self.ctx, Event.undo_event(2))

        eq_(self.ctx[0].hit, True)
        eq_(self.ctx[0].miss, False)
        check_char_list(self.ctx[0].input, [TEXT[0]])
        check_char_list(self.ctx[0].typos, [])

        eq_(self.ctx[1].hit, False)
        eq_(self.ctx[1].miss, True)
        check_char_list(self.ctx[1].input, [TEXT[2], '<UNDO>'])
        check_char_list(self.ctx[1].typos, [TEXT[2]])

        self.feedback_mock.assert_has_calls([
            call.on_hit(self.ctx, 0, TEXT[0]),
            call.on_miss(self.ctx, 1, TEXT[2], TEXT[1]),
            call.on_undo(self.ctx, 1, TEXT[1]),
        ])

    def test_undo_hit(self):
        process_event(self.ctx, Event.input_event(0, TEXT[0]))  # hit
        process_event(self.ctx, Event.undo_event(1))

        eq_(self.ctx[0].hit, False)
        eq_(self.ctx[0].miss, True)
        check_char_list(self.ctx[0].input, [TEXT[0], '<UNDO>'])

        check_char_list(self.ctx[0].typos, [])

        self.ctx[0]._undo_typo = True
        check_char_list(self.ctx[0].typos, ['<UNDO>'])

        self.feedback_mock.assert_has_calls([
            call.on_hit(self.ctx, 0, TEXT[0]),
            call.on_undo(self.ctx, 0, TEXT[0])
        ])

    def test_undo_fail_at_start(self):
        process_event(self.ctx, Event.undo_event(0))
        self.feedback_mock.assert_not_called()

    def test_end(self):
        text = TEXT + '\n'
        for i, c in enumerate(text):
            process_event(self.ctx, Event.input_event(i, c))
        eq_(self.ctx._state_fn, _state_end)
        self.feedback_mock.assert_has_calls([call.on_end(self.ctx)])

    def test_no_text(self):
        self.ctx = TrainingContext('')
        add_observer(self.ctx, self.feedback_mock)

        # Produce a miss at line end
        process_event(self.ctx, Event.input_event(0, TEXT[0]))  # miss
        eq_(self.ctx._state_fn, _state_input)

        eq_(self.ctx[0].hit, False)
        eq_(self.ctx[0].miss, True)
        eq_(self.ctx[0].input, [])
        eq_(self.ctx[0].typos, [])

        self.feedback_mock.assert_not_called()

    def test_newline(self):
        self.ctx = TrainingContext('\n')
        add_observer(self.ctx, self.feedback_mock)

        process_event(self.ctx, Event.input_event(0, 'A'))
        eq_(self.ctx._state_fn, _state_input)
        self.feedback_mock.assert_not_called()

    def test_index_out_of_range(self):
        assert_raises(IndexError, process_event, self.ctx, Event.input_event(len(TEXT) + 1, 'A'))
        eq_(self.ctx._state_fn, _state_input)
        self.feedback_mock.assert_not_called()

# def test_space(self):
# def test_linefeed(self):
