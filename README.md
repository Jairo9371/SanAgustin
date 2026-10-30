# Hospital San Agustín — Proyecto Django y SQL Server (CRUD completo)

Proyecto **académico**, generado a partir del archivo adjunto `Script_DDL_SanAgustin(1).sql`.
El script define `SanAgustinDB` con **30 tablas**: 25 con PK simple y 5 con PK compuesta.
Incluye conexión `mssql-django`, interfaz web responsive, autenticación, 30 módulos CRUD,
consultas parametrizadas, búsquedas, validaciones de formularios y confirmaciones antes de borrar.

> **Importante:** se entrega el código preparado y verificado estáticamente, **no una conexión ya establecida**.
> Para conectarlo se necesita instalar las dependencias en tu computadora, configurar
> la instancia de SQL Server y ejecutar las pruebas con tu usuario de base de datos.

## 1. Requisitos en Windows

- Python **3.10 a 3.14**, Windows 64 bits.
- Microsoft SQL Server (2017 o posterior recomendado) y SQL Server Management Studio (SSMS).
- **Microsoft ODBC Driver 18 for SQL Server**:
  https://learn.microsoft.com/es-es/sql/connect/odbc/download-odbc-driver-for-sql-server
- Visual Studio Code con extensión Python.

`mssql-django` versión 2.0 (septiembre de 2026) admite Django 5.2, 6.0 y 6.1;
el proyecto fija Django 5.2 para mantener la compatibilidad de Python indicada.
Puede instalar `mssql-django` 1.8 en plataformas donde 2.0 no sea compatible.

## 2. Crear la base de datos con tu script

1. Abre **SSMS** y conéctate a SQL Server.
2. Usa `sql/Script_DDL_SanAgustin.sql` y ejecútalo **una sola vez**.
3. Expande *Databases* → *SanAgustinDB* → *Tables*.
4. Deberán existir las 30 tablas (dbo.PACIENTE, dbo.MEDICO, dbo.CITA, etc.).

Si el script **ya fue ejecutado**, NO lo vuelvas a correr: contiene `CREATE TABLE`
y SQL Server indicaría que las tablas ya existen. Django no crea ni modifica
las 30 tablas originales, ya que sus modelos usan `managed = False`.

## 3. Preparar Python y abrir el proyecto en VS Code

Extrae este ZIP en una carpeta, por ejemplo `C:\Proyectos\Hospital_SanAgustin_Django_CRUD`.
Abre **File → Open Folder** en VS Code. Abre la terminal de PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Si PowerShell bloquea la activación, abre una terminal **CMD** e introduce
`.venv\Scripts\activate.bat`. Nunca subas `.env` al repositorio de GitHub.

## 4. Configurar SQL Server

Edita `.env` (aparece al copiar `.env.example`).

### Opción A — Autenticación de Windows (frecuente en SSMS)

```dotenv
DJANGO_DEBUG=true
SQL_HOST=DESKTOP-TU-PC\SQLEXPRESS
SQL_PORT=
SQL_DATABASE=SanAgustinDB
SQL_DRIVER=ODBC Driver 18 for SQL Server
SQL_USER=
SQL_PASSWORD=
SQL_TRUST_CERT=true
```

Cambia `DESKTOP-TU-PC\SQLEXPRESS` por el **Server name** de la ventana de conexión de SSMS.
Si SQL Server se ejecuta en instancia predeterminada, usa `SQL_HOST=localhost`.
La cuenta Windows que arranca Python debe tener permisos en la base.

### Opción B — SQL Server Authentication

```dotenv
SQL_HOST=localhost
SQL_PORT=
SQL_DATABASE=SanAgustinDB
SQL_DRIVER=ODBC Driver 18 for SQL Server
SQL_USER=usuario_de_sql
SQL_PASSWORD=contraseña_de_sql
SQL_TRUST_CERT=true
```

No copies claves reales dentro de archivos que compartirás. Usa cuentas de pocos privilegios.
`SQL_TRUST_CERT=true` solo es un ajuste para **desarrollo local** con certificados
sin cadena confiable; para producción debe ser `false` y usarse un certificado de confianza.

### Probar realmente la conexión

Si la base ya se creó con la versión anterior del DDL, actualiza el índice del
NIT para permitir varias aseguradoras sin NIT, manteniendo únicos los NIT informados:

```powershell
python manage.py actualizar_nit_opcional
```

Este comando utiliza la base configurada en `.env`, necesita permiso para alterar
el índice de `ASEGURADORA` y puede ejecutarse más de una vez. No elimina registros.
También puedes ejecutar `sql/actualizar_nit_opcional.sql` en SSMS, seleccionando
la base correcta. No vuelvas a ejecutar el DDL de creación sobre una base existente.
Las instalaciones nuevas ya incluyen el índice corregido en el DDL.

```powershell
python prueba_conexion.py
```

Este programa realiza `SELECT` de información de SQL Server, verifica la base activa,
las 30 tablas y la consulta a PACIENTE. Salida aproximada:

```text
Servidor: DESKTOP-TU-PC\SQLEXPRESS
Base de datos: SanAgustinDB
Tablas encontradas: 30/30
SELECT sobre PACIENTE: CORRECTO
CONEXIÓN Y ESTRUCTURA: OK
```

Los datos de servidor se mostrarán **solo si la conexión funciona**.

## 5. Migraciones de autenticación y arranque

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Las migraciones crean únicamente tablas de cuentas, permisos, sesiones y administración
de Django. No recrean `PACIENTE`, `MEDICO`, `FACTURA` ni ninguna tabla del script.

Abre **http://127.0.0.1:8000/** y entra con el superusuario creado.
La aplicación restringe acceso a los módulos hospitalarios a usuarios activos con
`is_staff=True`. Para el proyecto de clase, comienza usando el superusuario.

## 6. Módulos

| Área | Tablas incluidas |
|---|---|
| Pacientes y seguros | PACIENTE, CONDICION_CRONICA, PACIENTE_CONDICION, ALERGIA_PACIENTE, ASEGURADORA, POLIZA |
| Personal y sedes | SEDE, CONSULTORIO, ESPECIALIDAD, MEDICO, MEDICO_SUBESPECIALIDAD, TURNO, ENFERMERO |
| Atención médica | CITA, TRIAJE, DIAGNOSTICO_CIE10, CONSULTA, CONSULTA_DIAGNOSTICO |
| Farmacia y recetas | COMPONENTE_ACTIVO, MEDICAMENTO, MEDICAMENTO_COMPONENTE, RECETA, DETALLE_RECETA |
| Exámenes y procedimientos | CATALOGO_EXAMEN, ORDEN_EXAMEN, PROCEDIMIENTO, CONSULTA_PROCEDIMIENTO |
| Facturación | FACTURA, DETALLE_FACTURA, PAGO |

El panel principal muestra enlaces a las 30 tablas; cada pantalla permite:

- **Crear** (`INSERT`): botón `+ Nuevo registro` y formulario con controles según SQL.
- **Consultar** (`SELECT`): listado, detalles y búsqueda en las 25 tablas de PK simple.
- **Modificar** (`UPDATE`): botón `Editar` con datos existentes.
- **Eliminar** (`DELETE`): confirmación POST protegida con CSRF; las FK limitan el borrado.

En las **25 tablas con PK simple**, se emplea el ORM de Django (`objects`,
`ModelForm`, `save()` y `delete()`). En las **5 tablas con PK compuesta**,
`gestion/relaciones_crud.py` usa SQL *parametrizado* con `%s` para conservar
exactamente sus dos claves primarias y evitar limitaciones del backend.

### Cálculos de facturación

Primero crea una factura y después sus detalles. El subtotal de cada línea es
`cantidad × precio_unitario`; el subtotal de la factura es la suma de sus líneas.
Crear, editar, trasladar o eliminar un detalle actualiza esos importes en la misma
transacción. Los importes calculados se consultan en el detalle del registro.

La póliza debe pertenecer al paciente de la consulta. El deducible aplicado se
introduce manualmente después de agregar las líneas: la aseguradora cubre el
porcentaje de la póliza sobre `subtotal − deducible_aplicado`, con redondeo a
centavos; el resto corresponde al paciente. Sin póliza, todo corresponde al
paciente y el deducible debe ser cero. Por ejemplo, con subtotal de Q200,
deducible aplicado de Q20 y cobertura de 80%, corresponden Q144 a la aseguradora
y Q56 al paciente. Si al reducir las líneas el subtotal queda por debajo del
deducible aplicado, este se reduce al nuevo subtotal.

Los estados de cobro y los pagos se administran por separado. Estos cálculos no
modifican automáticamente los importes históricos hasta que se guarda la factura
o uno de sus detalles.

## 7. Cómo demostrar las cuatro sentencias

En la sección **Pacientes**:

1. Pulsa `+ Nuevo registro`, completa todos los campos marcados `*` y guarda.
2. Busca al paciente y abre su detalle (consulta SELECT).
3. Edita su teléfono y guarda (UPDATE).
4. Si no tiene relaciones dependientes, confirma `Eliminar` (DELETE).

En `sql/ejemplos_crud_paciente.sql` encontrarás además sentencias SQL reales para las
cuatro operaciones. El ejemplo emplea `BEGIN TRANSACTION` y `ROLLBACK` para evitar
dejar un paciente de demostración permanente.

**Pide evidencias para clase:** captura la configuración de SSMS sin mostrar
contraseñas; ejecución de `prueba_conexion.py`; tabla de pacientes; formulario
de creación; modificación; y confirmación de eliminación.

## 8. Organización

```text
Hospital_SanAgustin_Django_CRUD/
├── manage.py                     # Administración de Django
├── prueba_conexion.py           # Prueba SELECT real contra SQL Server
├── .env.example                 # Variables de conexión (sin credenciales reales)
├── requirements.txt             # Django, mssql-django, pyodbc, dotenv
├── inicio_windows.bat           # Arranque opcional en Windows
├── hospital/
│   ├── settings.py              # ENGINE='mssql' y credenciales por .env
│   └── urls.py                  # URLs principales y login
├── gestion/
│   ├── models.py                # Mapeo de 25 tablas existentes (managed=False)
│   ├── forms.py                 # Formularios y validaciones
│   ├── views.py                 # CRUD genérico de 25 tablas
│   ├── relaciones_crud.py       # CRUD SQL parametrizado de 5 tablas puente
│   ├── catalogo.py              # Tablas permitidas y menú
│   ├── urls.py                  # Enrutamiento de las 30 interfaces
│   └── tests.py                 # Pruebas estructurales de Django
├── templates/                   # HTML: dashboard, listados, detalle, formularios, login
├── static/css/estilos.css       # Estilos responsive
└── sql/
    ├── Script_DDL_SanAgustin.sql
    └── ejemplos_crud_paciente.sql
```

## 9. Validación local

Una vez instaladas las dependencias:

```powershell
python manage.py check
python manage.py test gestion --settings=hospital.test_settings
```

Las pruebas usan SQLite en memoria, sin acceder ni modificar SQL Server; incluyen
plantillas, paginación, validaciones y operaciones de facturación. No garantizan
la integración con SQL Server. Prueba `prueba_conexion.py` y los CRUD manualmente en una base
hospitalaria de ensayo para comprobar la integración y los permisos reales.

## 10. Errores comunes

| Error | Comprobación |
|---|---|
| `No module named django` | Activa `.venv` e instala `pip install -r requirements.txt`. |
| `Data source name not found` | Instala Microsoft ODBC Driver 18 o indica el driver ODBC correcto. |
| `Login failed for user` | Revisa autenticación Windows vs SQL, credenciales y permisos. |
| `Server was not found` | Revisa `SQL_HOST`, servicio SQL Server, TCP/IP y la instancia. |
| `certificate verify failed` | Configura TLS; solo en pruebas locales usa `SQL_TRUST_CERT=true`. |
| `Invalid object name PACIENTE` | Ejecuta el DDL en `SanAgustinDB` y comprueba `dbo`. |
| `Permission denied` | La cuenta requiere SELECT, INSERT, UPDATE y DELETE en tablas del sistema. |
| No permite eliminar | Alguna clave foránea de SQL Server protege el registro. |
| `migrate` falla con SQL Server | Comprueba si el login puede crear tablas de autenticación Django. |

## 11. Seguridad y alcance

**Uso académico con datos ficticios únicamente.** No usar información real de salud sin
implementar autorización granular por rol y paciente, auditoría de accesos/cambios,
retención documental, respaldos, cifrado, HTTPS y controles de privacidad aplicables.
El borrado físico de historias clínicas, pagos y prescripciones puede ser inadecuado
para un entorno hospitalario real: en producción se debería usar anulación/baja lógica
con trazabilidad, nunca permitir borrado indiscriminado.

Documentación técnica:
- https://github.com/microsoft/mssql-django
- https://learn.microsoft.com/en-us/sql/connect/python/mssql-django/python-sql-driver-mssql-django
- https://docs.djangoproject.com/en/5.2/topics/db/models/#meta-options
