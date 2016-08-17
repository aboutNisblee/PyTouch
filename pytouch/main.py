import sys
import os
from functools import partial
import argparse

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
root = partial(os.path.join, ROOT_PATH)


def run():
    from pytouch.model import get_engine, Session
    from pytouch.model.super import Base

    engine = get_engine({'sqlalchemy.url': 'sqlite:///tests.sqlite'})
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    from pytouch.service import CourseService

    CourseService.init_courses()
