from nose.tools import eq_
from pytouch.service import CourseService


class TestService(CourseService):
    _course_file_names = ('testcourse.xml', )

    def test_course_parser(self):
        tcs = list(self._parse_courses())
        eq_(len(tcs), 1)

        tc = tcs[0]
        eq_(tc.uuid, '{4e007d5e-613a-4a26-bff3-658d44d9cf10}')
        eq_(tc.title, 'TestCourse')
        eq_(tc.description, 'This file is only for testing purposes and will be filtered by application.')
        eq_(tc.builtin, True)
        eq_(tc.keyboard_layout, 'de')

        eq_(len(tc.lessons), 2)

        eq_(tc.lessons[0].uuid, '{d6e5a9a9-3c31-4175-8d58-245695c60b08}')
        eq_(tc.lessons[0].title, 'TestLesson1')
        eq_(tc.lessons[0].new_chars, 'fj')
        eq_(tc.lessons[0].builtin, True)
        eq_(tc.lessons[0].text, 'fff jjj')

        eq_(tc.lessons[1].uuid, '{e169c06b-71be-46df-97cf-8b3e68c5f75d}')
        eq_(tc.lessons[1].title, 'TestLesson2')
        eq_(tc.lessons[1].new_chars, 'dk')
        eq_(tc.lessons[1].builtin, True)
        eq_(tc.lessons[1].text, 'ddd kkk')
