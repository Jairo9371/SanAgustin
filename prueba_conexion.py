"""Comprueba credenciales, base de datos y las 30 tablas del DDL.

Comando: python prueba_conexion.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital.settings')
import django
django.setup()
from django.db import connection
from gestion.catalogo import MODELOS, RELACIONES

esperadas = {modelo._meta.db_table.upper() for modelo in MODELOS.values()}
esperadas.update(item['tabla'].upper() for item in RELACIONES.values())

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT DB_NAME(), @@SERVERNAME')
        bd, servidor = cursor.fetchone()
        cursor.execute('SELECT UPPER(name) FROM sys.tables WHERE schema_id = SCHEMA_ID(%s)', ['dbo'])
        encontradas = {fila[0] for fila in cursor.fetchall()}
        cursor.execute('SELECT TOP 1 [id_paciente] FROM [dbo].[PACIENTE]')
        cursor.fetchone()
except Exception as exc:
    print('ERROR al conectar/consultar SQL Server:')
    print(f'{type(exc).__name__}: {exc}')
    print('Verifica SQL_HOST, credenciales, SQL_DATABASE y Microsoft ODBC Driver 18.')
    sys.exit(1)

print(f'Servidor: {servidor}')
print(f'Base de datos: {bd}')
print(f'Tablas encontradas: {len(esperadas & encontradas)}/{len(esperadas)}')
print('SELECT sobre PACIENTE: CORRECTO')
if bd.lower() != 'sanagustindb':
    print('ADVERTENCIA: no es la base SanAgustinDB.')
if faltantes := sorted(esperadas - encontradas):
    print('FALTAN TABLAS:', ', '.join(faltantes))
    sys.exit(2)
print('CONEXIÓN Y ESTRUCTURA: OK')
