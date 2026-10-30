"""Instala el índice filtrado que permite varias aseguradoras sin NIT."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection


class Command(BaseCommand):
    help = 'Permite NIT vacíos en aseguradoras y conserva la unicidad de los NIT presentes.'

    def handle(self, *args, **options):
        if connection.vendor != 'microsoft':
            raise CommandError('Este ajuste requiere una base de datos SQL Server.')

        ruta = Path(settings.BASE_DIR) / 'sql' / 'actualizar_nit_opcional.sql'
        try:
            script = ruta.read_text(encoding='utf-8-sig')
        except OSError as exc:
            raise CommandError('No se encontró el script sql/actualizar_nit_opcional.sql.') from exc

        try:
            with connection.cursor() as cursor:
                cursor.execute(script)
        except DatabaseError as exc:
            raise CommandError(
                'No se pudo actualizar el índice del NIT. Comprueba que exista '
                'dbo.ASEGURADORA y que la cuenta tenga permiso ALTER sobre la tabla '
                'y no existan NIT duplicados. La operación es transaccional.'
            ) from exc

        self.stdout.write(self.style.SUCCESS(
            'Índice del NIT actualizado: se permiten varios NIT vacíos '
            'y los NIT presentes siguen siendo únicos.'
        ))
