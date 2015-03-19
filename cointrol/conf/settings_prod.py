"""
Cointrol production settings that extend the defaults ones.

"""
from .settings_defaults import *


DEBUG = False
TEMPLATE_DEBUG = False
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # Taken from django/utils/log.py:31
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'stdout': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG'
        }
    },

    'loggers': {
        'cointrol.trader': {
            'handlers': ['stdout', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}


COINTROL_DO_TRADE = True
