"""Comprueba el comando de ajuste del NIT sin modificar una base de datos."""
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import SimpleTestCase


class NitOpcionalTest(SimpleTestCase):
    modulo = 'gestion.management.commands.actualizar_nit_opcional'

    def test_rechaza_un_backend_distinto_de_sql_server(self):
        with patch(self.modulo + '.connection') as conexion:
            conexion.vendor = 'sqlite'
            with self.assertRaisesMessage(CommandError, 'requiere una base de datos SQL Server'):
                call_command('actualizar_nit_opcional')
            conexion.cursor.assert_not_called()

    def test_ejecuta_el_script_en_la_base_configurada(self):
        salida = StringIO()
        script = (Path(settings.BASE_DIR) / 'sql' / 'actualizar_nit_opcional.sql').read_text(
            encoding='utf-8-sig',
        )
        with patch(self.modulo + '.connection') as conexion:
            conexion.vendor = 'microsoft'
            cursor = conexion.cursor.return_value.__enter__.return_value
            call_command('actualizar_nit_opcional', stdout=salida)
            cursor.execute.assert_called_once_with(script)
        self.assertIn('se permiten varios NIT vacíos', salida.getvalue())

    def test_error_sql_no_imprime_detalles_de_conexion(self):
        salida = StringIO()
        with patch(self.modulo + '.connection') as conexion:
            conexion.vendor = 'microsoft'
            conexion.cursor.side_effect = DatabaseError('detalle privado de conexión')
            with self.assertRaises(CommandError) as error:
                call_command('actualizar_nit_opcional', stdout=salida)
        self.assertNotIn('detalle privado', str(error.exception))
        self.assertEqual(salida.getvalue(), '')
