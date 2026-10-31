"""Carga datos de demostración coherentes sin sobrescribir registros existentes."""
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from gestion.datos_prueba import FECHA_BASE, LOTE_PREDETERMINADO, cargar_datos_prueba


class Command(BaseCommand):
    help = 'Agrega pacientes y registros ficticios relacionados; repetir el mismo lote no duplica sus datos.'

    def add_arguments(self, parser):
        parser.add_argument('--pacientes', type=int, default=20, help='Cantidad de pacientes de prueba (1 a 100).')
        parser.add_argument('--lote', default=LOTE_PREDETERMINADO,
                            help='Identificador del lote, hasta 15 caracteres: mayúsculas, números y guiones.')
        parser.add_argument('--fecha-base', default=FECHA_BASE.isoformat(), help='Última fecha de consultas, AAAA-MM-DD.')
        parser.add_argument('--dry-run', action='store_true', help='Simula la operación y revierte sus cambios al terminar.')
        parser.add_argument('--naturalizar', action='store_true',
                            help='Actualiza solo los textos genéricos reconocidos del lote existente, sin crear registros.')

    def handle(self, *args, **options):
        try:
            resumen = cargar_datos_prueba(lote=options['lote'], pacientes=options['pacientes'],
                                         fecha_base=options['fecha_base'], dry_run=options['dry_run'],
                                         naturalizar=options['naturalizar'])
        except ValidationError as exc:
            raise CommandError('No se cargaron datos: ' + '; '.join(exc.messages)) from exc
        except DatabaseError as exc:
            raise CommandError('No se pudo cargar el lote; la transacción fue revertida. '
                               'Comprueba la conexión, las tablas y los identificadores únicos.') from exc
        prefijo = ('Simulación completada (sin guardar)' if resumen['simulacion'] else
                   'Textos actualizados' if options['naturalizar'] else 'Carga completada')
        self.stdout.write(self.style.SUCCESS(f'{prefijo}. Lote: {options["lote"]}'))
        tablas = sorted(set(resumen['creados']) | set(resumen['existentes']) | set(resumen['actualizados']))
        for tabla in tablas:
            self.stdout.write(f'{tabla}: {resumen["creados"].get(tabla, 0)} creados; '
                              f'{resumen["existentes"].get(tabla, 0)} existentes; '
                              f'{resumen["actualizados"].get(tabla, 0)} actualizados.')
        self.stdout.write(f'Total: {sum(resumen["creados"].values())} registros creados; '
                          f'{sum(resumen["existentes"].values())} existentes; '
                          f'{sum(resumen["actualizados"].values())} actualizados.')
