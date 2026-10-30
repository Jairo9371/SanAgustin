"""Pruebas aisladas en memoria; no abre la base de datos SQL Server."""
from .settings import *


DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
