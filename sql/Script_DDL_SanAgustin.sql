
IF DB_ID('SanAgustinDB') IS NULL
    CREATE DATABASE SanAgustinDB;
GO
USE SanAgustinDB;
GO

-- Paciente con expediente unico
CREATE TABLE PACIENTE (
    id_paciente                     INT IDENTITY(1,1) NOT NULL,
    num_expediente                  VARCHAR(20) NOT NULL,
    dpi                             VARCHAR(13) NOT NULL,
    nombres                         VARCHAR(80) NOT NULL,
    apellidos                       VARCHAR(80) NOT NULL,
    fecha_nacimiento                DATE NOT NULL,
    sexo                            CHAR(1) NOT NULL,
    tipo_sangre                     VARCHAR(3) NULL,
    direccion                       VARCHAR(200) NULL,
    telefono                        VARCHAR(15) NULL,
    correo                          VARCHAR(100) NULL,
    contacto_emergencia_nombre      VARCHAR(100) NOT NULL,
    contacto_emergencia_telefono    VARCHAR(15) NOT NULL,
    contacto_emergencia_parentesco  VARCHAR(30) NULL,
    fecha_registro                  DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_PACIENTE PRIMARY KEY (id_paciente),
    CONSTRAINT UQ_PACIENTE_num_expediente UNIQUE (num_expediente),
    CONSTRAINT UQ_PACIENTE_dpi UNIQUE (dpi)
);
GO

-- Catalogo de condiciones cronicas preexistentes
CREATE TABLE CONDICION_CRONICA (
    id_condicion                    INT IDENTITY(1,1) NOT NULL,
    nombre                          VARCHAR(100) NOT NULL,
    descripcion                     VARCHAR(250) NULL,
    CONSTRAINT PK_CONDICION_CRONICA PRIMARY KEY (id_condicion),
    CONSTRAINT UQ_CONDICION_CRONICA_nombre UNIQUE (nombre)
);
GO

-- Condiciones cronicas de cada paciente (N:M)
CREATE TABLE PACIENTE_CONDICION (
    id_paciente                     INT NOT NULL,
    id_condicion                    INT NOT NULL,
    fecha_diagnostico               DATE NULL,
    observaciones                   VARCHAR(250) NULL,
    CONSTRAINT PK_PACIENTE_CONDICION PRIMARY KEY (id_paciente, id_condicion),
    CONSTRAINT FK_PACIENTE_CONDICION_id_paciente FOREIGN KEY (id_paciente) REFERENCES PACIENTE(id_paciente),
    CONSTRAINT FK_PACIENTE_CONDICION_id_condicion FOREIGN KEY (id_condicion) REFERENCES CONDICION_CRONICA(id_condicion)
);
GO

-- Companias aseguradoras
CREATE TABLE ASEGURADORA (
    id_aseguradora                  INT IDENTITY(1,1) NOT NULL,
    nombre                          VARCHAR(100) NOT NULL,
    nit                             VARCHAR(15) NULL,
    telefono                        VARCHAR(15) NULL,
    correo                          VARCHAR(100) NULL,
    direccion                       VARCHAR(200) NULL,
    CONSTRAINT PK_ASEGURADORA PRIMARY KEY (id_aseguradora),
    CONSTRAINT UQ_ASEGURADORA_nombre UNIQUE (nombre)
);
GO
SET ANSI_NULLS ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET QUOTED_IDENTIFIER ON;
SET NUMERIC_ROUNDABORT OFF;
CREATE UNIQUE INDEX UQ_ASEGURADORA_nit
    ON dbo.ASEGURADORA(nit)
    WHERE nit IS NOT NULL;
GO

-- Poliza de un paciente con una aseguradora (numero de poliza y % de cobertura)
CREATE TABLE POLIZA (
    id_poliza                       INT IDENTITY(1,1) NOT NULL,
    id_paciente                     INT NOT NULL,
    id_aseguradora                  INT NOT NULL,
    numero_poliza                   VARCHAR(30) NOT NULL,
    porcentaje_cobertura            DECIMAL(5,2) NOT NULL,
    deducible                       DECIMAL(10,2) NOT NULL DEFAULT 0,
    fecha_inicio                    DATE NOT NULL,
    fecha_fin                       DATE NULL,
    estado                          VARCHAR(10) NOT NULL DEFAULT 'Activa',
    CONSTRAINT PK_POLIZA PRIMARY KEY (id_poliza),
    CONSTRAINT FK_POLIZA_id_paciente FOREIGN KEY (id_paciente) REFERENCES PACIENTE(id_paciente),
    CONSTRAINT FK_POLIZA_id_aseguradora FOREIGN KEY (id_aseguradora) REFERENCES ASEGURADORA(id_aseguradora)
);
GO

-- Sedes clinicas y centros de diagnostico
CREATE TABLE SEDE (
    id_sede                         INT IDENTITY(1,1) NOT NULL,
    nombre                          VARCHAR(100) NOT NULL,
    tipo                            VARCHAR(15) NOT NULL,
    direccion                       VARCHAR(200) NULL,
    municipio                       VARCHAR(60) NULL,
    departamento                    VARCHAR(60) NULL,
    telefono                        VARCHAR(15) NULL,
    CONSTRAINT PK_SEDE PRIMARY KEY (id_sede),
    CONSTRAINT UQ_SEDE_nombre UNIQUE (nombre)
);
GO

-- Consultorios de cada sede
CREATE TABLE CONSULTORIO (
    id_consultorio                  INT IDENTITY(1,1) NOT NULL,
    id_sede                         INT NOT NULL,
    numero                          VARCHAR(10) NOT NULL,
    piso                            VARCHAR(10) NULL,
    CONSTRAINT PK_CONSULTORIO PRIMARY KEY (id_consultorio),
    CONSTRAINT FK_CONSULTORIO_id_sede FOREIGN KEY (id_sede) REFERENCES SEDE(id_sede)
);
GO

-- Catalogo de especialidades medicas
CREATE TABLE ESPECIALIDAD (
    id_especialidad                 INT IDENTITY(1,1) NOT NULL,
    nombre                          VARCHAR(80) NOT NULL,
    descripcion                     VARCHAR(250) NULL,
    CONSTRAINT PK_ESPECIALIDAD PRIMARY KEY (id_especialidad),
    CONSTRAINT UQ_ESPECIALIDAD_nombre UNIQUE (nombre)
);
GO

-- Medico con colegiado activo y especialidad principal
CREATE TABLE MEDICO (
    id_medico                       INT IDENTITY(1,1) NOT NULL,
    num_colegiado                   VARCHAR(15) NOT NULL,
    nombres                         VARCHAR(80) NOT NULL,
    apellidos                       VARCHAR(80) NOT NULL,
    telefono                        VARCHAR(15) NULL,
    correo                          VARCHAR(100) NULL,
    id_especialidad                 INT NOT NULL,
    honorario_consulta              DECIMAL(10,2) NOT NULL DEFAULT 0,
    activo                          BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_MEDICO PRIMARY KEY (id_medico),
    CONSTRAINT UQ_MEDICO_num_colegiado UNIQUE (num_colegiado),
    CONSTRAINT FK_MEDICO_id_especialidad FOREIGN KEY (id_especialidad) REFERENCES ESPECIALIDAD(id_especialidad)
);
GO

-- Subespecialidades secundarias del medico (N:M)
CREATE TABLE MEDICO_SUBESPECIALIDAD (
    id_medico                       INT NOT NULL,
    id_especialidad                 INT NOT NULL,
    CONSTRAINT PK_MEDICO_SUBESPECIALIDAD PRIMARY KEY (id_medico, id_especialidad),
    CONSTRAINT FK_MEDICO_SUBESPECIALIDAD_id_medico FOREIGN KEY (id_medico) REFERENCES MEDICO(id_medico),
    CONSTRAINT FK_MEDICO_SUBESPECIALIDAD_id_especialidad FOREIGN KEY (id_especialidad) REFERENCES ESPECIALIDAD(id_especialidad)
);
GO

-- Turnos configurables del medico por consultorio/sede
CREATE TABLE TURNO (
    id_turno                        INT IDENTITY(1,1) NOT NULL,
    id_medico                       INT NOT NULL,
    id_consultorio                  INT NOT NULL,
    dia_semana                      TINYINT NOT NULL,
    hora_inicio                     TIME NOT NULL,
    hora_fin                        TIME NOT NULL,
    duracion_consulta_min           SMALLINT NOT NULL,
    activo                          BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_TURNO PRIMARY KEY (id_turno),
    CONSTRAINT FK_TURNO_id_medico FOREIGN KEY (id_medico) REFERENCES MEDICO(id_medico),
    CONSTRAINT FK_TURNO_id_consultorio FOREIGN KEY (id_consultorio) REFERENCES CONSULTORIO(id_consultorio)
);
GO

-- Personal de enfermeria que realiza el triaje
CREATE TABLE ENFERMERO (
    id_enfermero                    INT IDENTITY(1,1) NOT NULL,
    num_colegiado                   VARCHAR(15) NOT NULL,
    nombres                         VARCHAR(80) NOT NULL,
    apellidos                       VARCHAR(80) NOT NULL,
    telefono                        VARCHAR(15) NULL,
    id_sede                         INT NOT NULL,
    CONSTRAINT PK_ENFERMERO PRIMARY KEY (id_enfermero),
    CONSTRAINT UQ_ENFERMERO_num_colegiado UNIQUE (num_colegiado),
    CONSTRAINT FK_ENFERMERO_id_sede FOREIGN KEY (id_sede) REFERENCES SEDE(id_sede)
);
GO

-- Cita medica reservada de forma presencial o telefonica
CREATE TABLE CITA (
    id_cita                         INT IDENTITY(1,1) NOT NULL,
    id_paciente                     INT NOT NULL,
    id_medico                       INT NOT NULL,
    id_consultorio                  INT NOT NULL,
    id_turno                        INT NULL,
    fecha_hora_programada           DATETIME2 NOT NULL,
    canal_reserva                   VARCHAR(12) NOT NULL,
    motivo_consulta                 VARCHAR(250) NOT NULL,
    estado                          VARCHAR(15) NOT NULL DEFAULT 'Programada',
    fecha_creacion                  DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_CITA PRIMARY KEY (id_cita),
    CONSTRAINT FK_CITA_id_paciente FOREIGN KEY (id_paciente) REFERENCES PACIENTE(id_paciente),
    CONSTRAINT FK_CITA_id_medico FOREIGN KEY (id_medico) REFERENCES MEDICO(id_medico),
    CONSTRAINT FK_CITA_id_consultorio FOREIGN KEY (id_consultorio) REFERENCES CONSULTORIO(id_consultorio),
    CONSTRAINT FK_CITA_id_turno FOREIGN KEY (id_turno) REFERENCES TURNO(id_turno)
);
GO

-- Triaje de enfermeria previo a la consulta (signos vitales y urgencia)
CREATE TABLE TRIAJE (
    id_triaje                       INT IDENTITY(1,1) NOT NULL,
    id_cita                         INT NOT NULL,
    id_enfermero                    INT NOT NULL,
    fecha_hora_triaje               DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    peso_kg                         DECIMAL(5,2) NOT NULL,
    talla_cm                        DECIMAL(5,2) NOT NULL,
    presion_sistolica               SMALLINT NOT NULL,
    presion_diastolica              SMALLINT NOT NULL,
    frecuencia_cardiaca             SMALLINT NOT NULL,
    temperatura_c                   DECIMAL(4,1) NOT NULL,
    nivel_urgencia                  TINYINT NOT NULL,
    observaciones                   VARCHAR(250) NULL,
    CONSTRAINT PK_TRIAJE PRIMARY KEY (id_triaje),
    CONSTRAINT UQ_TRIAJE_id_cita UNIQUE (id_cita),
    CONSTRAINT FK_TRIAJE_id_cita FOREIGN KEY (id_cita) REFERENCES CITA(id_cita),
    CONSTRAINT FK_TRIAJE_id_enfermero FOREIGN KEY (id_enfermero) REFERENCES ENFERMERO(id_enfermero)
);
GO

-- Catalogo de diagnosticos CIE-10
CREATE TABLE DIAGNOSTICO_CIE10 (
    codigo_cie10                    VARCHAR(10) NOT NULL,
    descripcion                     VARCHAR(250) NOT NULL,
    CONSTRAINT PK_DIAGNOSTICO_CIE10 PRIMARY KEY (codigo_cie10)
);
GO

-- Nota medica de la consulta (expediente clinico)
CREATE TABLE CONSULTA (
    id_consulta                     INT IDENTITY(1,1) NOT NULL,
    id_cita                         INT NOT NULL,
    fecha_hora_consulta             DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    anamnesis                       VARCHAR(MAX) NOT NULL,
    examen_fisico                   VARCHAR(MAX) NULL,
    plan_tratamiento                VARCHAR(500) NULL,
    CONSTRAINT PK_CONSULTA PRIMARY KEY (id_consulta),
    CONSTRAINT UQ_CONSULTA_id_cita UNIQUE (id_cita),
    CONSTRAINT FK_CONSULTA_id_cita FOREIGN KEY (id_cita) REFERENCES CITA(id_cita)
);
GO

-- Diagnosticos de la consulta: principal y secundarios (N:M)
CREATE TABLE CONSULTA_DIAGNOSTICO (
    id_consulta                     INT NOT NULL,
    codigo_cie10                    VARCHAR(10) NOT NULL,
    tipo                            VARCHAR(10) NOT NULL,
    CONSTRAINT PK_CONSULTA_DIAGNOSTICO PRIMARY KEY (id_consulta, codigo_cie10),
    CONSTRAINT FK_CONSULTA_DIAGNOSTICO_id_consulta FOREIGN KEY (id_consulta) REFERENCES CONSULTA(id_consulta),
    CONSTRAINT FK_CONSULTA_DIAGNOSTICO_codigo_cie10 FOREIGN KEY (codigo_cie10) REFERENCES DIAGNOSTICO_CIE10(codigo_cie10)
);
GO

-- Catalogo de principios activos
CREATE TABLE COMPONENTE_ACTIVO (
    id_componente                   INT IDENTITY(1,1) NOT NULL,
    nombre                          VARCHAR(100) NOT NULL,
    CONSTRAINT PK_COMPONENTE_ACTIVO PRIMARY KEY (id_componente),
    CONSTRAINT UQ_COMPONENTE_ACTIVO_nombre UNIQUE (nombre)
);
GO

-- Catalogo de la farmacia hospitalaria con su existencia
CREATE TABLE MEDICAMENTO (
    id_medicamento                  INT IDENTITY(1,1) NOT NULL,
    nombre_comercial                VARCHAR(100) NOT NULL,
    forma_farmaceutica              VARCHAR(30) NULL,
    concentracion                   VARCHAR(30) NULL,
    precio_unitario                 DECIMAL(10,2) NOT NULL,
    stock_farmacia                  INT NOT NULL DEFAULT 0,
    activo                          BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_MEDICAMENTO PRIMARY KEY (id_medicamento)
);
GO

-- Componentes activos de cada medicamento (N:M)
CREATE TABLE MEDICAMENTO_COMPONENTE (
    id_medicamento                  INT NOT NULL,
    id_componente                   INT NOT NULL,
    CONSTRAINT PK_MEDICAMENTO_COMPONENTE PRIMARY KEY (id_medicamento, id_componente),
    CONSTRAINT FK_MEDICAMENTO_COMPONENTE_id_medicamento FOREIGN KEY (id_medicamento) REFERENCES MEDICAMENTO(id_medicamento),
    CONSTRAINT FK_MEDICAMENTO_COMPONENTE_id_componente FOREIGN KEY (id_componente) REFERENCES COMPONENTE_ACTIVO(id_componente)
);
GO

-- Receta electronica vinculada a la consulta
CREATE TABLE RECETA (
    id_receta                       INT IDENTITY(1,1) NOT NULL,
    id_consulta                     INT NOT NULL,
    fecha_emision                   DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    estado                          VARCHAR(12) NOT NULL DEFAULT 'Emitida',
    CONSTRAINT PK_RECETA PRIMARY KEY (id_receta),
    CONSTRAINT UQ_RECETA_id_consulta UNIQUE (id_consulta),
    CONSTRAINT FK_RECETA_id_consulta FOREIGN KEY (id_consulta) REFERENCES CONSULTA(id_consulta)
);
GO

-- Medicamentos prescritos: dosis, via, frecuencia y duracion
CREATE TABLE DETALLE_RECETA (
    id_detalle_receta               INT IDENTITY(1,1) NOT NULL,
    id_receta                       INT NOT NULL,
    id_medicamento                  INT NOT NULL,
    dosis                           VARCHAR(50) NOT NULL,
    via_administracion              VARCHAR(20) NOT NULL,
    frecuencia_horas                SMALLINT NOT NULL,
    duracion_dias                   SMALLINT NOT NULL,
    cantidad_despachar              INT NOT NULL,
    CONSTRAINT PK_DETALLE_RECETA PRIMARY KEY (id_detalle_receta),
    CONSTRAINT FK_DETALLE_RECETA_id_receta FOREIGN KEY (id_receta) REFERENCES RECETA(id_receta),
    CONSTRAINT FK_DETALLE_RECETA_id_medicamento FOREIGN KEY (id_medicamento) REFERENCES MEDICAMENTO(id_medicamento)
);
GO

-- Catalogo de examenes de laboratorio e imagenes
CREATE TABLE CATALOGO_EXAMEN (
    id_examen                       INT IDENTITY(1,1) NOT NULL,
    nombre                          VARCHAR(100) NOT NULL,
    tipo                            VARCHAR(12) NOT NULL,
    precio                          DECIMAL(10,2) NOT NULL,
    CONSTRAINT PK_CATALOGO_EXAMEN PRIMARY KEY (id_examen),
    CONSTRAINT UQ_CATALOGO_EXAMEN_nombre UNIQUE (nombre)
);
GO

-- Ordenes de laboratorio o imagenes solicitadas en la consulta
CREATE TABLE ORDEN_EXAMEN (
    id_orden                        INT IDENTITY(1,1) NOT NULL,
    id_consulta                     INT NOT NULL,
    id_examen                       INT NOT NULL,
    fecha_solicitud                 DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    estado                          VARCHAR(12) NOT NULL DEFAULT 'Solicitado',
    resultado                       VARCHAR(500) NULL,
    CONSTRAINT PK_ORDEN_EXAMEN PRIMARY KEY (id_orden),
    CONSTRAINT FK_ORDEN_EXAMEN_id_consulta FOREIGN KEY (id_consulta) REFERENCES CONSULTA(id_consulta),
    CONSTRAINT FK_ORDEN_EXAMEN_id_examen FOREIGN KEY (id_examen) REFERENCES CATALOGO_EXAMEN(id_examen)
);
GO

-- Catalogo de procedimientos medicos
CREATE TABLE PROCEDIMIENTO (
    id_procedimiento                INT IDENTITY(1,1) NOT NULL,
    nombre                          VARCHAR(100) NOT NULL,
    precio                          DECIMAL(10,2) NOT NULL,
    CONSTRAINT PK_PROCEDIMIENTO PRIMARY KEY (id_procedimiento),
    CONSTRAINT UQ_PROCEDIMIENTO_nombre UNIQUE (nombre)
);
GO

-- Procedimientos realizados en la consulta (N:M)
CREATE TABLE CONSULTA_PROCEDIMIENTO (
    id_consulta                     INT NOT NULL,
    id_procedimiento                INT NOT NULL,
    cantidad                        INT NOT NULL DEFAULT 1,
    CONSTRAINT PK_CONSULTA_PROCEDIMIENTO PRIMARY KEY (id_consulta, id_procedimiento),
    CONSTRAINT FK_CONSULTA_PROCEDIMIENTO_id_consulta FOREIGN KEY (id_consulta) REFERENCES CONSULTA(id_consulta),
    CONSTRAINT FK_CONSULTA_PROCEDIMIENTO_id_procedimiento FOREIGN KEY (id_procedimiento) REFERENCES PROCEDIMIENTO(id_procedimiento)
);
GO

-- Orden de cobro / factura con desglose de aseguradora y paciente
CREATE TABLE FACTURA (
    id_factura                      INT IDENTITY(1,1) NOT NULL,
    numero_factura                  VARCHAR(20) NOT NULL,
    id_consulta                     INT NOT NULL,
    id_poliza                       INT NULL,
    fecha_emision                   DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    tipo                            VARCHAR(7) NOT NULL DEFAULT 'Total',
    subtotal                        DECIMAL(12,2) NOT NULL DEFAULT 0,
    deducible_aplicado              DECIMAL(12,2) NOT NULL DEFAULT 0,
    monto_aseguradora               DECIMAL(12,2) NOT NULL DEFAULT 0,
    monto_paciente                  DECIMAL(12,2) NOT NULL DEFAULT 0,
    estado_pago_paciente            VARCHAR(10) NOT NULL DEFAULT 'Pendiente',
    estado_cobro_aseguradora        VARCHAR(10) NOT NULL DEFAULT 'NoAplica',
    CONSTRAINT PK_FACTURA PRIMARY KEY (id_factura),
    CONSTRAINT UQ_FACTURA_numero_factura UNIQUE (numero_factura),
    CONSTRAINT FK_FACTURA_id_consulta FOREIGN KEY (id_consulta) REFERENCES CONSULTA(id_consulta),
    CONSTRAINT FK_FACTURA_id_poliza FOREIGN KEY (id_poliza) REFERENCES POLIZA(id_poliza)
);
GO

-- Lineas de la factura: honorarios, procedimientos, medicamentos y examenes
CREATE TABLE DETALLE_FACTURA (
    id_detalle_factura              INT IDENTITY(1,1) NOT NULL,
    id_factura                      INT NOT NULL,
    tipo_concepto                   VARCHAR(13) NOT NULL,
    descripcion                     VARCHAR(200) NOT NULL,
    id_medicamento                  INT NULL,
    id_examen                       INT NULL,
    id_procedimiento                INT NULL,
    cantidad                        INT NOT NULL DEFAULT 1,
    precio_unitario                 DECIMAL(10,2) NOT NULL,
    subtotal_linea                  DECIMAL(12,2) NOT NULL,
    CONSTRAINT PK_DETALLE_FACTURA PRIMARY KEY (id_detalle_factura),
    CONSTRAINT FK_DETALLE_FACTURA_id_factura FOREIGN KEY (id_factura) REFERENCES FACTURA(id_factura),
    CONSTRAINT FK_DETALLE_FACTURA_id_medicamento FOREIGN KEY (id_medicamento) REFERENCES MEDICAMENTO(id_medicamento),
    CONSTRAINT FK_DETALLE_FACTURA_id_examen FOREIGN KEY (id_examen) REFERENCES CATALOGO_EXAMEN(id_examen),
    CONSTRAINT FK_DETALLE_FACTURA_id_procedimiento FOREIGN KEY (id_procedimiento) REFERENCES PROCEDIMIENTO(id_procedimiento)
);
GO

-- Pagos aplicados a una factura (paciente o aseguradora)
CREATE TABLE PAGO (
    id_pago                         INT IDENTITY(1,1) NOT NULL,
    id_factura                      INT NOT NULL,
    fecha_pago                      DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    monto                           DECIMAL(12,2) NOT NULL,
    pagador                         VARCHAR(10) NOT NULL,
    metodo                          VARCHAR(15) NOT NULL,
    referencia                      VARCHAR(50) NULL,
    CONSTRAINT PK_PAGO PRIMARY KEY (id_pago),
    CONSTRAINT FK_PAGO_id_factura FOREIGN KEY (id_factura) REFERENCES FACTURA(id_factura)
);
GO

-- Alergias conocidas del paciente a un componente activo
CREATE TABLE ALERGIA_PACIENTE (
    id_alergia                      INT IDENTITY(1,1) NOT NULL,
    id_paciente                     INT NOT NULL,
    id_componente                   INT NOT NULL,
    reaccion                        VARCHAR(150) NULL,
    severidad                       VARCHAR(10) NULL,
    CONSTRAINT PK_ALERGIA_PACIENTE PRIMARY KEY (id_alergia),
    CONSTRAINT FK_ALERGIA_PACIENTE_id_paciente FOREIGN KEY (id_paciente) REFERENCES PACIENTE(id_paciente),
    CONSTRAINT FK_ALERGIA_PACIENTE_id_componente FOREIGN KEY (id_componente) REFERENCES COMPONENTE_ACTIVO(id_componente)
);
GO
