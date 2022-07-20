import debug_toolbar
from django.conf.global_settings import INTERNAL_IPS

from core.settings.common import *

DEBUG = True
PROD = False

INSTALLED_APPS.append('debug_toolbar')
INSTALLED_APPS.append('django_extensions')
MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

INTERNAL_IPS.append('127.0.0.1')