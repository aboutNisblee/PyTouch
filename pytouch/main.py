import logging
import argparse

import sys

from pytouch.model import get_engine, Session, reset_db
from pytouch.gui.tk import window


def init_db(args):
    db_uri = getattr(args, 'database')
    logging.debug('Database URI: {}'.format(db_uri))
    engine = get_engine({'sqlalchemy.url': db_uri})
    Session.configure(bind=engine)


def reset_database(args):
    from pytouch.service import CourseService

    init_db(args)
    reset_db()
    CourseService.init_courses()


def run(args=None):
    init_db(args)
    window.MainWindow().show()


def manage():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('--verbose', '-v', action='count', default=0, help='Increase verbosity')
    verbosity_group.add_argument('--quiet', '-q', action='store_true', help='Reduce verbosity')

    # FIXME: Database path incorrect! Depends on installation path!
    parser.add_argument('--database', type=str, default='sqlite:///tests.sqlite', help='Change the default database')
    parser.set_defaults(fun=run)

    parser_setup = subparsers.add_parser('reset-database')
    parser_setup.set_defaults(fun=reset_database)

    args = parser.parse_args()

    lut_verbosity = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    level = logging.FATAL if getattr(args, 'quiet') else lut_verbosity.get(getattr(args, 'verbose', 0), logging.DEBUG)
    # logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=level, format='%(name)s: %(levelname)s: %(message)s')

    logging.info('Configuration:\n\t{}'.format('\n\t'.join(['{}: {}'.format(k, getattr(v, '__name__', v)) for k, v in sorted(args.__dict__.items())])))

    args.fun(args)
