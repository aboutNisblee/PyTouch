import argparse

import sys

from pytouch.model import get_engine, Session, reset_db
from pytouch.gui.tk import window


def init_db(arg_map):
    engine = get_engine({'sqlalchemy.url': arg_map['database']})
    Session.configure(bind=engine)


def reset_database(arg_map):
    from pytouch.service import CourseService

    init_db(arg_map)
    reset_db()
    CourseService.init_courses()


def run(arg_map=None):
    init_db(arg_map)
    window.MainWindow().show()


def manage():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # FIXME: Database path incorrect! Depends on installation path!
    parser.add_argument('--database', type=str, default='sqlite:///tests.sqlite', help='Change the default database')
    parser.set_defaults(fun=run)

    parser_setup = subparsers.add_parser('reset-database')
    parser_setup.set_defaults(fun=reset_database)

    args = parser.parse_args()
    if not args.fun:
        parser.print_help()
        sys.exit()

    arg_map = vars(args).copy()
    arg_map.pop('fun')

    args.fun(arg_map)
