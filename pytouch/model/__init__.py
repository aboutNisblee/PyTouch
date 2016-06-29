from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import configure_mappers
from sqlalchemy.engine import Engine
from sqlalchemy import engine_from_config
from sqlalchemy import event

# import or define all models here to ensure they are attached to the
# Base.metadata prior to any initialization routines
from .course import Course, LessonList, Lesson
from .profile import Profile
from .meta import Meta


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# run configure_mappers after defining all of the models to ensure
# all relationships can be setup
configure_mappers()


def get_engine(settings=None, prefix='sqlalchemy.'):
    if settings is None:
        settings = {'sqlalchemy.url': 'sqlite:///declarative_m2m_ordered_list.sqlite'}
    return engine_from_config(settings, prefix)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory
