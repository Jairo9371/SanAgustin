"""Configuración para desarrollo; cambie las variables de entorno para producción."""
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'solo-desarrollo-configura-una-clave-segura')
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'
if not DEBUG and SECRET_KEY in ('solo-desarrollo-configura-una-clave-segura', 'cambia-esta-clave-por-una-cadena-aleatoria-segura'):
    raise RuntimeError('Configura DJANGO_SECRET_KEY segura antes de publicar.')
ALLOWED_HOSTS = [x.strip() for x in os.getenv('DJANGO_ALLOWED_HOSTS','127.0.0.1,localhost').split(',') if x.strip()]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if x.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gestion',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'hospital.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ]},
    },
]
WSGI_APPLICATION = 'hospital.wsgi.application'
ASGI_APPLICATION = 'hospital.asgi.application'

# Vaciar SQL_USER / SQL_PASSWORD para Autenticación de Windows (trusted connection).
# Para SQL Authentication, indicar ambos valores en .env.
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': os.getenv('SQL_DATABASE','SanAgustinDB'),
        'HOST': os.getenv('SQL_HOST','localhost'),
        'PORT': os.getenv('SQL_PORT',''),
        'USER': os.getenv('SQL_USER',''),
        'PASSWORD': os.getenv('SQL_PASSWORD',''),
        'OPTIONS': {
          'driver': 'ODBC Driver 17 for SQL Server',  
            'extra_params': 'TrustServerCertificate=yes;Encrypt=yes;',
        },
            'connection_timeout': 10,
            'connection_retries': 1,
        },
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guatemala'
# SQL DATETIME2 del DDL usa SYSDATETIME() sin zona; trabajar con fechas locales ingenuas.
USE_TZ = False
USE_I18N = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'gestion:inicio'
LOGOUT_REDIRECT_URL = 'login'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
