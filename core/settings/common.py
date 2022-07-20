import os

from unipath import Path

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).parent.parent.parent
BASE_URL = os.getenv('SERVER', 'localhost:8000')

# load production server from .env
ALLOWED_HOSTS = ['localhost', '127.0.0.1', os.getenv('SERVER', '127.0.0.1')]

SECRET_KEY = os.getenv('SECRET_KEY', 'S#perS3crEt_1122')

INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # My Apps
    'authentication',
    'ticket',

    # Third Party Apps
    'mptt',
    'hijack',
    'background_task',
    'crispy_forms'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Disables for teams
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Third Party
    # Tracking last edited and created by users in models
    'django_currentuser.middleware.ThreadLocalUserMiddleware',
]

# CSRF Settings for MS Teams to work properly
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True

# Session Cookie Settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'

ROOT_URLCONF = 'core.urls'
LOGIN_REDIRECT_URL = "home"  # Route defined in ticket/urls.py
LOGOUT_REDIRECT_URL = "home"  # Route defined in ticket/urls.py
CORE_TEMPLATE_DIR = os.path.join(BASE_DIR, "core", "templates")  # ROOT dir for templates
TICKET_TEMPLATE_DIR = os.path.join(BASE_DIR, "ticket", "templates")  # ROOT dir for templates
AUTH_TEMPLATE_DIR = os.path.join(BASE_DIR, "authentication", "templates")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [CORE_TEMPLATE_DIR, TICKET_TEMPLATE_DIR, AUTH_TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Ticket Notifications
                'ticket.context_processor.top_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'de-de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = False

APPEND_SLASH = True

#############################################################
# SRC: https://devcenter.heroku.com/articles/django-assets

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'core', 'static'),
)

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
#############################################################
# EMAIL SETTINGS
EMAIL_HOST = "SMTP.office365.com"
EMAIL_PORT = "587"
EMAIL_HOST_USER = os.getenv('EMAIL_ADDRESS', "x@y.com")
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', "fakepassword")
EMAIL_USE_TLS = True
#############################################################

# AZURE APP SETTINGS
#############################################################
AZURE_APP_ID = os.getenv("AZURE_APP_ID", "123456789")


RANDOM_TIMES = False
