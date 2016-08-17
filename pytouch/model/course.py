import uuid
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from .super import Base


class Lesson(Base):
    __tablename__ = 'tblLesson'

    uuid = Column('pkLessonUuid', String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column('cLessonTitle', String, nullable=False)
    new_chars = Column('cNewChars', String)
    builtin = Column('cLessonBuiltin', Boolean, default=False)
    text = Column('cText', String)
    course = relationship('LessonList', backref=backref('lesson'), cascade="all, delete-orphan")

    def __repr__(self):
        return '{self.uuid} -- builtin: {self.builtin!s:>5} -- {self.title}'.format(self=self)


class LessonList(Base):
    __tablename__ = 'tblLessonList'

    id = Column('pkLessonListId', Integer, primary_key=True, autoincrement=True)
    course_uuid = Column('fkCourseUuid', String, ForeignKey('tblCourse.pkCourseUuid', onupdate='CASCADE', ondelete='CASCADE'))
    lesson_uuid = Column('fkLessonUuid', String, ForeignKey('tblLesson.pkLessonUuid', onupdate='CASCADE', ondelete='CASCADE'))
    position = Column('position', Integer)

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
    keyboard_layout = Column('cKbLayout', String)
    _lessons = relationship(LessonList, backref=backref('course'), cascade="all, delete-orphan", order_by=LessonList.position, collection_class=ordering_list('position'))
    lessons = association_proxy('_lessons', 'lesson')

    def __repr__(self):
        return '{self.uuid} -- builtin: {self.builtin!s:>5} -- lesson count: {lessons:2} -- {self.title}'.format(self=self, lessons=len(self.lessons))

    @staticmethod
    def find_all(session):
        return session.query(Course)
