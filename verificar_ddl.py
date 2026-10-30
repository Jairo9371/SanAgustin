"""Auditoría estática sin dependencias de la coincidencia Django ↔ DDL.

Uso: python verificar_ddl.py
No sustituye una prueba real de SQL Server.
"""
from __future__ import annotations
import ast
import re
from pathlib import Path

ROOT = Path(__file__).parent
sql = (ROOT / 'sql/Script_DDL_SanAgustin.sql').read_text(encoding='utf-8-sig')
mod = ast.parse((ROOT / 'gestion/models.py').read_text(encoding='utf-8'))
cat = ast.parse((ROOT / 'gestion/catalogo.py').read_text(encoding='utf-8'))

# Extraer tablas y columnas de CREATE TABLE del archivo suministrado.
tablas = {}
for nombre, bloque in re.findall(r'CREATE TABLE\s+(\w+)\s*\((.*?)\n\);', sql, re.S | re.I):
    columnas = []
    for linea in bloque.splitlines():
        m = re.match(r'\s*(\w+)\s+(?:INT|VARCHAR\(MAX\)|VARCHAR\(\d+\)|CHAR\(\d+\)|'
                     r'DECIMAL\(\d+,\d+\)|DATETIME2|DATE|TIME|TINYINT|SMALLINT|BIT)\s+', linea)
        if m:
            columnas.append(m.group(1))
    tablas[nombre] = columnas

modelos = {}
for clase in mod.body:
    if not isinstance(clase, ast.ClassDef):
        continue
    columnas = set()
    tabla = None
    for nodo in clase.body:
        if isinstance(nodo, ast.Assign) and isinstance(nodo.value, ast.Call):
            if isinstance(nodo.value.func, ast.Attribute) and isinstance(nodo.value.func.value, ast.Name):
                if nodo.value.func.value.id == 'models':
                    columnas.update(t.id for t in nodo.targets if isinstance(t, ast.Name))
        if isinstance(nodo, ast.ClassDef) and nodo.name == 'Meta':
            for prop in nodo.body:
                if isinstance(prop, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'db_table' for t in prop.targets):
                    tabla = ast.literal_eval(prop.value)
    if tabla:
        modelos[tabla] = columnas

relaciones = None
for nodo in cat.body:
    if isinstance(nodo, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RELACIONES' for t in nodo.targets):
        relaciones = ast.literal_eval(nodo.value)

fallos = []
if len(tablas) != 30 or len(modelos) != 25 or len(relaciones) != 5:
    fallos.append(f'Cantidad de tablas: DDL={len(tablas)} modelos={len(modelos)} puentes={len(relaciones)}')
for tabla, cols in modelos.items():
    esperadas = set(tablas.get(tabla, []))
    if esperadas != cols:
        fallos.append(f'{tabla}: faltan {sorted(esperadas-cols)}, sobran {sorted(cols-esperadas)}')
for slug, item in relaciones.items():
    tabla = item['tabla']
    if tablas.get(tabla) != item['columnas']:
        fallos.append(f'{slug}: columnas de tabla puente diferentes al DDL')
if set(tablas) != set(modelos) | {dato['tabla'] for dato in relaciones.values()}:
    fallos.append('Las tablas cubiertas no coinciden con el DDL completo.')

print(f'DDL original: {len(tablas)} tablas')
print(f'Django ORM:  {len(modelos)} modelos con PK simple')
print(f'SQL directo: {len(relaciones)} tablas de PK compuesta')
if fallos:
    print('ERRORES EN EL MAPEO:')
    for error in fallos:
        print(' -', error)
    raise SystemExit(1)
print('MAPEO DE TABLAS Y COLUMNAS: CORRECTO (30/30)')
