-- EJEMPLO ACADÉMICO: operaciones básicas sobre el DDL real.
-- Ejecutar solo con base de PRUEBA y respaldo. Siempre se revierte al final.
USE SanAgustinDB;
GO
BEGIN TRANSACTION;

-- CREATE / INSERT (campos requeridos por PACIENTE)
INSERT INTO dbo.PACIENTE (
    num_expediente, dpi, nombres, apellidos, fecha_nacimiento, sexo,
    contacto_emergencia_nombre, contacto_emergencia_telefono
) VALUES (
    'DEMO-001', '0000000000001', 'Prueba', 'Django', '2000-01-01', 'F',
    'Contacto Prueba', '55550000'
);

DECLARE @id INT = SCOPE_IDENTITY();

-- READ / SELECT
SELECT id_paciente, num_expediente, nombres, apellidos, telefono
FROM dbo.PACIENTE WHERE id_paciente = @id;

-- UPDATE
UPDATE dbo.PACIENTE SET telefono = '44445555' WHERE id_paciente = @id;

-- DELETE
DELETE FROM dbo.PACIENTE WHERE id_paciente = @id;

-- Revertir por seguridad: no dejar datos de demostración.
ROLLBACK TRANSACTION;
GO
