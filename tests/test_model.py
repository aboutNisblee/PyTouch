from random import randrange

from nose.tools import eq_
from pytouch.model import Course, LessonList, Lesson, Profile, Meta, get_engine, get_session_factory
from pytouch.model.super import Base


class TestDbMapper(object):
    def __init__(self):
        self.s = None

    @classmethod
    def setup_class(cls):
        cls.e = get_engine({'sqlalchemy.url': 'sqlite:///tests.sqlite'})
        # cls.e = get_engine()
        cls.f = get_session_factory(cls.e)

    def setup(self):
        Base.metadata.drop_all(self.e)
        Base.metadata.create_all(self.e)
        self.s = self.f()

    def teardown(self):
        self.s.close()

    def test_lesson_order(self):
        uut = Course(title='uut')
        self.s.add(uut)

        uut.lessons = [Lesson(title=i) for i in range(10)]

        self.s.commit()
        self.s.refresh(uut)

        eq_([lesson.title for lesson in uut.lessons], [str(i) for i in range(10)])

        n = randrange(9)
        # Pop a random lesson an append it to the end
        uut.lessons.append(uut.lessons.pop(n))

        self.s.commit()

        # Build a list of numbers with the same order we expect the lesson names in db
        cmp = [str(i) for i in range(10)]
        cmp.append(cmp.pop(n))

        self.s.refresh(uut)
        eq_([lesson.title for lesson in uut.lessons], cmp)

    def test_drop_lesson_from_course(self):
        uut = Course(title='uut')
        self.s.add(uut)
        uut.lessons = [Lesson(title=i) for i in range(10)]
        self.s.commit()

        uut.lessons.pop()
        self.s.commit()
        self.s.refresh(uut)

        eq_(9, self.s.query(LessonList).count())
        eq_(10, self.s.query(Lesson).count())

    def test_delete_lesson(self):
        uut = Course(title='uut')
        self.s.add(uut)
        uut.lessons = [Lesson(title=i) for i in range(10)]
        self.s.commit()

        # Delete the last lesson that is held by Course object
        self.s.delete(uut.lessons[-1])
        self.s.commit()

        eq_(9, self.s.query(Lesson).count())
        eq_(9, self.s.query(LessonList).count())
        # lessons of uut are expired by commit and updated by unit of work on next access
        # therefore the we can expect 9 lessons when we access the uut.
        eq_(9, len(uut.lessons))
        eq_(9, len(self.s.query(Course).one().lessons))
