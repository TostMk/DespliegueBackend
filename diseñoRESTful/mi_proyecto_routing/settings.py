SECRET_KEY = 'django-insecure-local-practice-key'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'juego',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]
ROOT_URLCONF = 'mi_proyecto_routing.urls'
TEMPLATES = []
WSGI_APPLICATION = 'mi_proyecto_routing.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
