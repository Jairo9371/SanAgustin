-- Ejecutar en la base hospitalaria existente. No cambia ni elimina datos.
-- Puede repetirse: conserva el índice correcto si ya está instalado.
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET QUOTED_IDENTIFIER ON;
SET NUMERIC_ROUNDABORT OFF;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @tabla INT = OBJECT_ID(N'dbo.ASEGURADORA', N'U');
    IF @tabla IS NULL
        THROW 50001, 'No existe dbo.ASEGURADORA en la base seleccionada.', 1;

    IF EXISTS (
        SELECT 1 FROM sys.key_constraints
        WHERE parent_object_id = @tabla
          AND name = N'UQ_ASEGURADORA_nit'
          AND type = 'UQ'
    )
        ALTER TABLE dbo.ASEGURADORA DROP CONSTRAINT UQ_ASEGURADORA_nit;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = @tabla AND name = N'UQ_ASEGURADORA_nit'
    )
        CREATE UNIQUE INDEX UQ_ASEGURADORA_nit
            ON dbo.ASEGURADORA(nit)
            WHERE nit IS NOT NULL;
    ELSE IF NOT EXISTS (
        SELECT 1 FROM sys.indexes AS indice
        WHERE indice.object_id = @tabla
          AND indice.name = N'UQ_ASEGURADORA_nit'
          AND indice.is_unique = 1
          AND indice.is_disabled = 0
          AND indice.has_filter = 1
          AND UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
              indice.filter_definition, N' ', N''), N'[', N''), N']', N''),
              N'(', N''), N')', N'')) = N'NITISNOTNULL'
          AND (SELECT COUNT(*) FROM sys.index_columns AS clave
               WHERE clave.object_id = indice.object_id
                 AND clave.index_id = indice.index_id
                 AND clave.key_ordinal > 0) = 1
          AND EXISTS (
              SELECT 1 FROM sys.index_columns AS clave
              INNER JOIN sys.columns AS columna
                  ON columna.object_id = clave.object_id
                 AND columna.column_id = clave.column_id
              WHERE clave.object_id = indice.object_id
                AND clave.index_id = indice.index_id
                AND clave.key_ordinal = 1
                AND columna.name = N'nit'
          )
    )
        THROW 50002, 'UQ_ASEGURADORA_nit ya existe con otra definición. No se modificó.', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
