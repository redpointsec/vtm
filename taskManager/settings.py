# Vulnerable Task Manager

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from datetime import timedelta
import redis
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = '0yxzudryd8)-%)(fz&7q-!v&cq1u6vbfoc4u7@u_&i)b@4eh^q'
SECRET_KEY = 'secret'
# Disable debug in certain environments

DEBUG = True

# ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ALLOWED_HOSTS = ['*']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'mysite.log',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'DEBUG',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django.contrib.sessions',
    'django_filters',
    'taskManager',
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'health_check.contrib.migrations',
    'health_check.contrib.psutil',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',  # Added for JWT support
    'drf_spectacular',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',  # Required for Django admin
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Only needed if using CSRF tokens
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'taskManager.middleware.JWTAuthenticationMiddleware'
)

ROOT_URLCONF = 'taskManager.urls'

WSGI_APPLICATION = 'taskManager.wsgi.application'

FILE_UPLOAD_HANDLERS = (
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",)

# Database

DATABASES = {
    # For SQLite
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'vtmdb.sqlite3',
    }

    # For MySQL
    # 'default': {
    #    'ENGINE': 'django.db.backends.mysql',
    #    'NAME': 'vtmdb',
    #    'USER': 'root',
    #    'PASSWORD': '',
    #    'HOST': 'localhost'
    # }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = '/tmp/static-tm'

STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = STATIC_URL + "admin/"

MEDIA_ROOT = '/tmp/static-tm/taskManager/uploads'
MEDIA_URL = '/uploads/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "taskManager/static"),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGIN_URL = '/taskManager/login/'
# LOGIN_REDIRECT_URL = '/taskManager/dashboard/'

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

ADMINS = [
  ('Happy Admin', 'admin@tm.com')
]

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),  # Extremely long-lived token
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),  # Long refresh token lifetime
    'ROTATE_REFRESH_TOKENS': False,  # Disable rotation of refresh tokens
    'BLACKLIST_AFTER_ROTATION': False,  # Disable token blacklisting
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Task Manager API',
    'DESCRIPTION': 'Task Manager API for reporting',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Set up Redis connection (adjust host and port as needed)
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
