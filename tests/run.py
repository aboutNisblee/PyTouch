#!/bin/env python3
import sys
import os

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))

if __name__ == '__main__':
    import nose

    nose.run(argv=sys.argv.insert(1, ROOT_PATH))
