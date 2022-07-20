from huey import SqliteHuey

from core.settings.common import *

DEBUG = False
PROD = True if not DEBUG else False

INSTALLED_APPS.append('huey.contrib.djhuey')

DATABASES = {
    'default': {
        'ENGINE': os.getenv("POSTGRES_BACKEND", "postgres"),
        'NAME': os.getenv("POSTGRES_NAME", "postgres"),
        'USER': os.getenv("POSTGRES_USER", "postgres"),
        'PASSWORD': os.getenv("POSTGRES_PASSWORD", "postgres"),
        'HOST': os.getenv("POSTGRES_HOST", "postgres"),
        'PORT': os.getenv("POSTGRES_PORT", "postgres"),
    }
}

HUEY = SqliteHuey(name='huey.db')