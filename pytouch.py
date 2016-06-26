#!/bin/env python3
import sys
import uuid
from functools import partial
from random import randrange

from nose.tools import eq_
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import sessionmaker, relationship, backref


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


Base = declarative_base()


class Meta(Base):
    __tablename__ = 'tblMeta'

    key = Column('pkKey', String, primary_key=True)
    value = Column('cValue', String)


class Profile(Base):
    __tablename__ = 'tblProfile'

    name = Column('pkProfileName', String, primary_key=True)
    skillLevel = Column('cSkillLevel', Integer, nullable=False, default=0)


class Lesson(Base):
    __tablename__ = 'tblLesson'

    uuid = Column('pkLessonUuid', String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column('cLessonTitle', String, nullable=False)
    newChars = Column('cNewChars', String)
    builtin = Column('cLessonBuiltin', Boolean, default=False)
    text = Column('cText', String)


class LessonList(Base):
    __tablename__ = 'tblLessonList'

    id = Column('pkLessonListId', Integer, primary_key=True, autoincrement=True)
    courseUuid = Column('fkCourseUuid', String, ForeignKey('tblCourse.pkCourseUuid', onupdate='CASCADE', ondelete='CASCADE'))
    lessonUuid = Column('fkLessonUuid', String, ForeignKey('tblLesson.pkLessonUuid', onupdate='CASCADE', ondelete='CASCADE'))
    position = Column('position', Integer)
    lesson = relationship(Lesson, backref='course')

    def __init__(self, lesson=None, **kw):
        if lesson is not None:
            kw['lesson'] = lesson
            Base.__init__(self, **kw)


class Course(Base):
    __tablename__ = 'tblCourse'

    uuid = Column('pkCourseUuid', String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column('cCourseTitle', String, nullable=False)
    description = Column('cDescription', String)
    builtin = Column('cCourseBuiltin', Boolean, default=False)
    _lessons = relationship(LessonList, backref=backref('course'), cascade="all, delete-orphan", order_by=LessonList.position, collection_class=ordering_list('position'))
    lessons = association_proxy('_lessons', 'lesson')


engine = create_engine('sqlite:///declarative_m2m_ordered_list.db')
session = sessionmaker()
session.configure(bind=engine)

create_all = partial(Base.metadata.create_all, engine)
drop_all = partial(Base.metadata.drop_all, engine)


class TestDbMapper():
    def __init__(self):
        self.s = None

    def setup(self):
        drop_all()
        create_all()
        self.s = session()

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

        # Build a list of numbers with the same order we expect the lesson names get db
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

        self.s.delete(uut.lessons.pop())
        self.s.commit()

        eq_(9, self.s.query(Lesson).count())
        eq_(9, self.s.query(LessonList).count())
        eq_(9, len(self.s.query(Course).one().lessons))


if __name__ == '__main__':
    import nose

    nose.run(argv=sys.argv.insert(1, __file__))
