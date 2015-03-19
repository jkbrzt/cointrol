import sys


try:
    from .settings_local import *
except ImportError as e:
    sys.stderr.write("""
ERROR: It looks like settings_local.py is missing:

    {}

""".format(str(e)))

    sys.exit(1)
