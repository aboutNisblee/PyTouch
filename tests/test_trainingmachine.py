from datetime import datetime, timedelta
from unittest.mock import MagicMock, call

from nose.tools import eq_, assert_raises, assert_almost_equal, assert_list_equal

from pytouch.trainingmachine import *

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
        self.uut = TrainingMachine(TEXT, auto_unpause=True)
        self.uut.add_observer(self.feedback_mock)

    def test_init(self):
        for i, c in enumerate(TEXT + '\n'):
            eq_(self.uut._text[i].index, i)
            eq_(self.uut._text[i].char, c)
            eq_(self.uut._text[i].hit, False)
            eq_(self.uut._text[i].miss, True)
            check_char_list(self.uut._text[i].keystrokes, [])
            check_char_list(self.uut._text[i].typos, [])

    def test_pause(self):
        # First unpause since we are starting in pause state.
        self.uut.process_event(Event.unpause_event())
        eq_(self.uut._state_fn, self.uut._state_input)
        eq_(self.uut._pause_history[-1].action, 'start')
        assert_almost_equal(self.uut._pause_history[-1].time,
                            datetime.utcnow(), delta=timedelta(milliseconds=5))

        # pause and check inner state change
        self.uut.process_event(Event.pause_event())
        eq_(self.uut._state_fn, self.uut._state_pause)
        eq_(self.uut._pause_history[-1].action, 'pause')
        assert_almost_equal(self.uut._pause_history[-1].time,
                            datetime.utcnow(), delta=timedelta(milliseconds=5))

        # unpause and check inner state change
        self.uut.process_event(Event.unpause_event())
        eq_(self.uut._state_fn, self.uut._state_input)
        eq_(self.uut._pause_history[-1].action, 'unpause')
        assert_almost_equal(self.uut._pause_history[-1].time,
                            datetime.utcnow(), delta=timedelta(milliseconds=5))

        # check feedback
        self.feedback_mock.assert_has_calls(
            [call.on_unpause(self.uut), call.on_pause(self.uut),
             call.on_unpause(self.uut)])

    def test_hit(self):
        self.uut.process_event(Event.input_event(0, TEXT[0]))
        eq_(self.uut._state_fn, self.uut._state_input)
        eq_(self.uut._text[0].hit, True)
        eq_(self.uut._text[0].miss, False)
        check_char_list(self.uut._text[0].keystrokes, [TEXT[0]])
        check_char_list(self.uut._text[0].typos, [])
        self.feedback_mock.assert_has_calls([call.on_hit(self.uut, 0, TEXT[0])])

    def test_miss(self):
        self.uut.process_event(Event.input_event(0, TEXT[1]))
        eq_(self.uut._state_fn, self.uut._state_input)
        eq_(self.uut._text[0].hit, False)
        eq_(self.uut._text[0].miss, True)
        check_char_list(self.uut._text[0].keystrokes, [TEXT[1]])
        check_char_list(self.uut._text[0].typos, [TEXT[1]])
        self.feedback_mock.assert_has_calls([call.on_miss(self.uut, 0, TEXT[1], TEXT[0])])

    def test_undo_miss(self):
        self.uut.process_event(Event.input_event(0, TEXT[0]))  # hit
        self.uut.process_event(Event.input_event(1, TEXT[2]))  # miss
        self.uut.process_event(Event.undo_event(2))

        eq_(self.uut._text[0].hit, True)
        eq_(self.uut._text[0].miss, False)
        check_char_list(self.uut._text[0].keystrokes, [TEXT[0]])
        check_char_list(self.uut._text[0].typos, [])

        eq_(self.uut._text[1].hit, False)
        eq_(self.uut._text[1].miss, True)
        check_char_list(self.uut._text[1].keystrokes, [TEXT[2], '<UNDO>'])
        check_char_list(self.uut._text[1].typos, [TEXT[2]])

        self.feedback_mock.assert_has_calls([
            call.on_hit(self.uut, 0, TEXT[0]),
            call.on_miss(self.uut, 1, TEXT[2], TEXT[1]),
            call.on_undo(self.uut, 1, TEXT[1]),
        ])

    def test_undo_hit(self):
        self.uut.process_event(Event.input_event(0, TEXT[0]))  # hit
        self.uut.process_event(Event.undo_event(1))

        eq_(self.uut._text[0].hit, False)
        eq_(self.uut._text[0].miss, True)
        check_char_list(self.uut._text[0].keystrokes, [TEXT[0], '<UNDO>'])

        check_char_list(self.uut._text[0].typos, [])

        self.uut._text[0]._undo_typo = True
        check_char_list(self.uut._text[0].typos, ['<UNDO>'])

        self.feedback_mock.assert_has_calls([
            call.on_hit(self.uut, 0, TEXT[0]),
            call.on_undo(self.uut, 0, TEXT[0])
        ])

    def test_undo_fail_at_start(self):
        self.uut.process_event(Event.undo_event(0))
        self.feedback_mock.assert_not_called()

    def test_end(self):
        text = TEXT + '\n'
        for i, c in enumerate(text):
            self.uut.process_event(Event.input_event(i, c))
        eq_(self.uut._state_fn, self.uut._state_end)
        self.feedback_mock.assert_has_calls([call.on_end(self.uut)])

    def test_no_text(self):
        self.uut = TrainingMachine('', auto_unpause=True)
        self.uut.add_observer(self.feedback_mock)

        # Produce a miss at line end
        self.uut.process_event(Event.input_event(0, TEXT[0]))  # miss
        eq_(self.uut._state_fn, self.uut._state_input)

        eq_(self.uut._text[0].hit, False)
        eq_(self.uut._text[0].miss, True)
        eq_(self.uut._text[0].keystrokes, [])
        eq_(self.uut._text[0].typos, [])

        self.feedback_mock.assert_not_called()

    def test_newline(self):
        self.uut = TrainingMachine('\n', auto_unpause=True)
        self.uut.add_observer(self.feedback_mock)

        self.uut.process_event(Event.input_event(0, 'A'))
        eq_(self.uut._state_fn, self.uut._state_input)
        self.feedback_mock.assert_not_called()

    def test_index_out_of_range(self):
        assert_raises(IndexError, self.uut.process_event, Event.input_event(len(TEXT) + 1, 'A'))
        eq_(self.uut._state_fn, self.uut._state_input)
        self.feedback_mock.assert_not_called()

# def test_space(self):
# def test_linefeed(self):
