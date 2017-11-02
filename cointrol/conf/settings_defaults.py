"""
Cointrol default settings.

"""
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
AUTH_USER_MODEL = 'core.User'
ROOT_URLCONF = 'cointrol.server.urls'
INSTALLED_APPS = [
    'django_extensions',
    'rest_framework',
    'cointrol.core',
    'cointrol.server',
    'cointrol.trader',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

]
MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Copenhagen'
USE_I18N = False
USE_L10N = True
USE_TZ = True
WEBAPP_DIR = os.path.join(BASE_DIR, 'webapp')
WEBAPP_STATIC_DIR = os.path.join(WEBAPP_DIR, 'public')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    WEBAPP_STATIC_DIR
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS':
        'cointrol.server.api.pagination.CointrolPagination',
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
