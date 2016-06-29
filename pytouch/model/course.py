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
