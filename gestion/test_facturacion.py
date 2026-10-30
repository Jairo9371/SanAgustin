"""Regresiones monetarias y CRUD aislado de SQL Server."""
from datetime import date, datetime
from decimal import Decimal
from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import SimpleTestCase, TransactionTestCase

from .catalogo import MODELOS
from .facturacion import calcular_importes, subtotal_de_linea
from .models import (Aseguradora, Cita, Consulta, Consultorio, DetalleFactura,
                     Especialidad, Factura, Medico, Paciente, Poliza, Sede, Triaje, Turno)


class CalculosFacturaTest(SimpleTestCase):
    def test_reparto_redondea_sin_perder_centavos(self):
        self.assertEqual(calcular_importes('0.03', '0', '50'),
                         (Decimal('0.02'), Decimal('0.01')))
        self.assertEqual(calcular_importes('200', '50', '80'),
                         (Decimal('120.00'), Decimal('80.00')))

    def test_lineas_rechazan_negativos_y_desbordamientos(self):
        for cantidad, precio in [(0, '100'), (-1, '100'), (1, '-1'),
                                 (1, '1.001'), (2147483648, '1'), (101, '99999999.99')]:
            with self.subTest(cantidad=cantidad, precio=precio), self.assertRaises(ValidationError):
                subtotal_de_linea(cantidad, precio)

    def test_rangos_tinyint(self):
        for modelo, campo, valido, invalido in [(Turno, 'dia_semana', 7, 8),
                                               (Triaje, 'nivel_urgencia', 255, 256)]:
            campo = modelo._meta.get_field(campo)
            campo.run_validators(valido)
            with self.assertRaises(ValidationError):
                campo.run_validators(invalido)


@skipUnless(connection.vendor == 'sqlite', 'Usa --settings=hospital.test_settings para estas pruebas aisladas.')
class FacturaIntegracionTest(TransactionTestCase):
    # El runner no debe crear una base SQL de pruebas al usar settings normales.
    databases = {'default'} if connection.vendor == 'sqlite' else set()

    def setUp(self):
        super().setUp()
        with connection.schema_editor() as editor:
            for modelo in MODELOS.values():
                editor.create_model(modelo)
        paciente = self.crear_paciente('1')
        sede = Sede.objects.create(nombre='Sede de prueba', tipo='Clinica')
        consultorio = Consultorio.objects.create(id_sede=sede, numero='1')
        especialidad = Especialidad.objects.create(nombre='General')
        medico = Medico.objects.create(num_colegiado='1', nombres='Médico', apellidos='Prueba',
                                       id_especialidad=especialidad)
        cita = Cita.objects.create(id_paciente=paciente, id_medico=medico, id_consultorio=consultorio,
                                  fecha_hora_programada=datetime(2026, 10, 26, 10),
                                  canal_reserva='Presencial', motivo_consulta='Prueba')
        self.consulta = Consulta.objects.create(id_cita=cita, anamnesis='Prueba')
        aseguradora = Aseguradora.objects.create(nombre='Seguro prueba', nit='1')
        self.poliza = Poliza.objects.create(id_paciente=paciente, id_aseguradora=aseguradora,
                                           numero_poliza='1', porcentaje_cobertura=Decimal('80'),
                                           fecha_inicio=date(2026, 1, 1))

    def tearDown(self):
        try:
            with connection.schema_editor() as editor:
                for modelo in reversed(list(MODELOS.values())):
                    editor.delete_model(modelo)
        finally:
            super().tearDown()

    @staticmethod
    def crear_paciente(numero):
        return Paciente.objects.create(num_expediente=numero, dpi=numero.zfill(13), nombres='Paciente',
            apellidos=numero, fecha_nacimiento=date(1990, 1, 1), sexo='M',
            contacto_emergencia_nombre='Contacto', contacto_emergencia_telefono='12345678')

    def crear_factura(self, numero='1', con_poliza=True):
        return Factura.objects.create(numero_factura=numero, id_consulta=self.consulta,
                                      id_poliza=self.poliza if con_poliza else None)

    @staticmethod
    def crear_detalle(factura, cantidad=2, precio='100.00'):
        return DetalleFactura.objects.create(id_factura=factura, tipo_concepto='Consulta',
            descripcion='Honorarios', cantidad=cantidad, precio_unitario=Decimal(precio))

    def test_crear_detalle_calcula_linea_totales_y_cobertura(self):
        factura = self.crear_factura()
        detalle = self.crear_detalle(factura)
        self.assertEqual(detalle.subtotal_linea, Decimal('200.00'))
        factura.refresh_from_db()
        self.assertEqual((factura.subtotal, factura.monto_aseguradora, factura.monto_paciente),
                         (Decimal('200.00'), Decimal('160.00'), Decimal('40.00')))
        factura.deducible_aplicado = Decimal('50')
        factura.save(update_fields={'deducible_aplicado'})
        factura.refresh_from_db()
        self.assertEqual((factura.monto_aseguradora, factura.monto_paciente),
                         (Decimal('120.00'), Decimal('80.00')))

    def test_editar_y_update_fields_usan_los_datos_realmente_guardados(self):
        factura = self.crear_factura()
        detalle = self.crear_detalle(factura)
        detalle.cantidad = 3
        detalle.save(update_fields={'cantidad'})
        detalle.refresh_from_db()
        self.assertEqual(detalle.subtotal_linea, Decimal('300.00'))
        detalle.cantidad = 999  # No está incluido en la actualización siguiente.
        detalle.descripcion = 'Descripción nueva'
        detalle.save(update_fields={'descripcion'})
        detalle.refresh_from_db()
        factura.refresh_from_db()
        self.assertEqual(detalle.cantidad, 3)
        self.assertEqual(factura.subtotal, Decimal('300.00'))

    def test_trasladar_detalle_recalcula_ambas_facturas(self):
        anterior = self.crear_factura()
        nueva = self.crear_factura('2', con_poliza=False)
        detalle = self.crear_detalle(anterior)
        detalle.id_factura = nueva
        detalle.save(update_fields={'id_factura'})
        anterior.refresh_from_db()
        nueva.refresh_from_db()
        self.assertEqual(anterior.subtotal, Decimal('0.00'))
        self.assertEqual((nueva.subtotal, nueva.monto_aseguradora, nueva.monto_paciente),
                         (Decimal('200.00'), Decimal('0.00'), Decimal('200.00')))

    def test_eliminar_detalle_recalcula_y_limita_el_deducible(self):
        factura = self.crear_factura()
        detalle = self.crear_detalle(factura)
        factura.refresh_from_db()
        factura.deducible_aplicado = Decimal('80')
        factura.save()
        detalle.delete()
        factura.refresh_from_db()
        self.assertEqual((factura.subtotal, factura.deducible_aplicado,
                          factura.monto_aseguradora, factura.monto_paciente),
                         (Decimal('0.00'),) * 4)

    def test_eliminar_objeto_obsoleto_recalcula_la_factura_actual(self):
        anterior = self.crear_factura()
        nueva = self.crear_factura('2')
        detalle = self.crear_detalle(anterior)
        obsoleto = DetalleFactura.objects.get(pk=detalle.pk)
        detalle.id_factura = nueva
        detalle.save()
        obsoleto.delete()
        anterior.refresh_from_db()
        nueva.refresh_from_db()
        self.assertEqual((anterior.subtotal, nueva.subtotal), (Decimal('0.00'), Decimal('0.00')))

    def test_rechaza_poliza_de_otro_paciente(self):
        self.poliza.id_paciente = self.crear_paciente('2')
        self.poliza.save()
        with self.assertRaises(ValidationError) as error:
            self.crear_factura()
        self.assertIn('id_poliza', error.exception.message_dict)
        self.assertFalse(Factura.objects.exists())

    def test_desbordamiento_del_total_revierte_el_detalle(self):
        factura = self.crear_factura()
        self.crear_detalle(factura, cantidad=60, precio='99999999.99')
        with self.assertRaises(ValidationError):
            self.crear_detalle(factura, cantidad=60, precio='99999999.99')
        factura.refresh_from_db()
        self.assertEqual(DetalleFactura.objects.count(), 1)
        self.assertEqual(factura.subtotal, Decimal('5999999999.40'))
