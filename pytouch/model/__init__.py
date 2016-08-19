from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import configure_mappers
from sqlalchemy.engine import Engine
from sqlalchemy import engine_from_config
from sqlalchemy import event

# import or define all models here to ensure they are attached to the
# Base.metadata prior to any initialization routines
from pytouch.model.course import Course, LessonList, Lesson
from pytouch.model.profile import Profile
from pytouch.model.meta import Meta


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
        settings = {'sqlalchemy.url': 'sqlite:///:memory:'}
    return engine_from_config(settings, prefix)


Session = sessionmaker()


@contextmanager
def session_scope(*args, **kwargs):
    """Provide a transactional scope around a series of operations.

    Additional arguments are passed to session factory making to possible to e.g. changing the engine.
    """
    session = Session(*args, **kwargs)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
