"""Carga de demostración aislada; nunca crea ni modifica una base SQL Server."""
from datetime import date
from decimal import Decimal
from io import StringIO
from unittest import skipUnless
from unittest.mock import patch

from django.core.validators import validate_email
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase, TransactionTestCase

from . import models
from .catalogo import MODELOS, RELACIONES
from .models import Cita, Consulta, DetalleFactura, Factura, Paciente, Pago, Poliza, Triaje
from .perfiles_prueba import perfil_paciente


TABLAS_PUENTE = (
    '''CREATE TABLE PACIENTE_CONDICION (
        id_paciente INTEGER NOT NULL REFERENCES PACIENTE(id_paciente),
        id_condicion INTEGER NOT NULL REFERENCES CONDICION_CRONICA(id_condicion),
        fecha_diagnostico DATE NULL, observaciones VARCHAR(250) NULL,
        PRIMARY KEY (id_paciente, id_condicion))''',
    '''CREATE TABLE MEDICO_SUBESPECIALIDAD (
        id_medico INTEGER NOT NULL REFERENCES MEDICO(id_medico),
        id_especialidad INTEGER NOT NULL REFERENCES ESPECIALIDAD(id_especialidad),
        PRIMARY KEY (id_medico, id_especialidad))''',
    '''CREATE TABLE CONSULTA_DIAGNOSTICO (
        id_consulta INTEGER NOT NULL REFERENCES CONSULTA(id_consulta),
        codigo_cie10 VARCHAR(10) NOT NULL REFERENCES DIAGNOSTICO_CIE10(codigo_cie10),
        tipo VARCHAR(10) NOT NULL, PRIMARY KEY (id_consulta, codigo_cie10))''',
    '''CREATE TABLE MEDICAMENTO_COMPONENTE (
        id_medicamento INTEGER NOT NULL REFERENCES MEDICAMENTO(id_medicamento),
        id_componente INTEGER NOT NULL REFERENCES COMPONENTE_ACTIVO(id_componente),
        PRIMARY KEY (id_medicamento, id_componente))''',
    '''CREATE TABLE CONSULTA_PROCEDIMIENTO (
        id_consulta INTEGER NOT NULL REFERENCES CONSULTA(id_consulta),
        id_procedimiento INTEGER NOT NULL REFERENCES PROCEDIMIENTO(id_procedimiento),
        cantidad INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (id_consulta, id_procedimiento))''',
)


class PerfilesPruebaTest(SimpleTestCase):
    def test_cien_identidades_distintas_con_contactos_validos(self):
        perfiles = [perfil_paciente(numero) for numero in range(1, 101)]
        self.assertEqual(len({(perfil['nombres'], perfil['apellidos']) for perfil in perfiles}), 100)
        self.assertEqual(len({perfil['correo'] for perfil in perfiles}), 100)
        for numero, perfil in enumerate(perfiles, 1):
            with self.subTest(numero=numero):
                self.assertNotRegex(perfil['nombres'] + perfil['apellidos'], r'[0-9]')
                validate_email(perfil['correo'])
                self.assertTrue(perfil['correo'].endswith('@example.com'))
                for campo, valor in perfil.items():
                    self.assertTrue(valor)
                    self.assertLessEqual(len(valor), Paciente._meta.get_field(campo).max_length)


@skipUnless(connection.vendor == 'sqlite', 'Usa --settings=hospital.test_settings para las pruebas aisladas.')
class DatosPruebaTest(TransactionTestCase):
    # Django inspecciona databases incluso en clases omitidas: no habilitar SQL Server.
    databases = {'default'} if connection.vendor == 'sqlite' else set()

    def setUp(self):
        super().setUp()
        with connection.schema_editor() as editor:
            for modelo in MODELOS.values():
                editor.create_model(modelo)
        with connection.cursor() as cursor:
            for sentencia in TABLAS_PUENTE:
                cursor.execute(sentencia)

    def tearDown(self):
        try:
            with connection.cursor() as cursor:
                for relacion in reversed(list(RELACIONES.values())):
                    cursor.execute('DROP TABLE ' + relacion['tabla'])
            with connection.schema_editor() as editor:
                for modelo in reversed(list(MODELOS.values())):
                    editor.delete_model(modelo)
        finally:
            super().tearDown()

    def cargar(self, **opciones):
        argumentos = {'lote': 'DEMO-20261030', 'pacientes': 2, 'fecha_base': date(2026, 10, 30)}
        argumentos.update(opciones)
        salida = StringIO()
        call_command('cargar_datos_prueba', stdout=salida, **argumentos)
        return salida.getvalue()

    @staticmethod
    def estado():
        """Comparar todos los campos detecta cambios, no solo filas duplicadas."""
        estado = {
            modelo._meta.db_table: list(modelo.objects.order_by(modelo._meta.pk.name).values())
            for modelo in MODELOS.values()
        }
        with connection.cursor() as cursor:
            for relacion in RELACIONES.values():
                orden = ', '.join(relacion['columnas'][:2])
                cursor.execute('SELECT * FROM ' + relacion['tabla'] + ' ORDER BY ' + orden)
                estado[relacion['tabla']] = cursor.fetchall()
        return estado

    def estado_protegido(self):
        """La presentación puede cambiar; identidades, relaciones e importes no."""
        estado = self.estado()
        claves_texto = {'num_expediente', 'dpi', 'numero_factura', 'num_colegiado',
                        'numero_poliza', 'nit', 'codigo_cie10'}
        for modelo in MODELOS.values():
            campos = {
                campo.attname for campo in modelo._meta.fields
                if (campo.primary_key or campo.is_relation or campo.name in claves_texto
                    or campo.get_internal_type() not in ('CharField', 'TextField'))
            }
            estado[modelo._meta.db_table] = [
                {campo: valor for campo, valor in fila.items() if campo in campos}
                for fila in estado[modelo._meta.db_table]
            ]
        # Las observaciones de esta relación también se naturalizan.
        estado['PACIENTE_CONDICION'] = [fila[:3] for fila in estado['PACIENTE_CONDICION']]
        return estado

    def preparar_textos_anteriores(self):
        """Representar un lote ya instalado antes de incorporar los perfiles."""
        paciente = Paciente.objects.get(num_expediente='DEMO-20261030-001')
        Paciente.objects.filter(pk=paciente.pk).update(
            nombres='Paciente de prueba 001', apellidos='DEMO-20261030',
            direccion='Dirección ficticia; registro de demostración', telefono='00000000',
            correo='paciente001@example.com', contacto_emergencia_nombre='Contacto ficticio de prueba',
            contacto_emergencia_telefono='00000000', contacto_emergencia_parentesco='Familiar de prueba',
        )
        cita = Cita.objects.filter(id_paciente=paciente).order_by('fecha_hora_programada').first()
        Cita.objects.filter(pk=cita.pk).update(motivo_consulta='DEMO-20261030: cita de prueba 001-1')
        Consulta.objects.filter(id_cita=cita).update(
            anamnesis='DEMO-20261030: historia de prueba del paciente 001, visita 1.',
            examen_fisico='Examen simulado; datos exclusivamente de demostración.',
            plan_tratamiento='Plan ficticio de prueba; no constituye una indicación médica.',
        )
        Triaje.objects.filter(id_cita=cita).update(observaciones='Triaje ficticio para demostración.')
        factura = Factura.objects.get(numero_factura='DEMO-20261030-F001')
        for detalle in DetalleFactura.objects.filter(id_factura=factura):
            DetalleFactura.objects.filter(pk=detalle.pk).update(
                descripcion=f'DEMO-20261030: {detalle.tipo_concepto} de prueba')
        sede = models.Sede.objects.order_by('pk').first()
        models.Sede.objects.filter(pk=sede.pk).update(
            nombre='DEMO-20261030 PRUEBA sede 1',
            direccion='Dirección ficticia para demostración', municipio='Municipio de prueba',
            departamento='Departamento de prueba', telefono='00000000',
        )
        componente = models.ComponenteActivo.objects.order_by('pk').first()
        models.ComponenteActivo.objects.filter(pk=componente.pk).update(
            nombre='DEMO-20261030 PRUEBA componente 1')
        with connection.cursor() as cursor:
            cursor.execute('UPDATE PACIENTE_CONDICION SET observaciones = %s WHERE id_paciente = %s',
                           ['Relación ficticia de prueba.', paciente.pk])
        return paciente, cita, sede

    def test_carga_nueva_presenta_nombres_contactos_y_expedientes_naturales(self):
        self.cargar()
        paciente = Paciente.objects.get(num_expediente='DEMO-20261030-001')
        self.assertEqual(paciente.nombres, 'Ana Lucía')
        self.assertEqual(paciente.apellidos, 'Morales Castillo')
        self.assertEqual(paciente.contacto_emergencia_nombre, 'Marta Elena Castillo')
        self.assertIn('zona', paciente.direccion)
        self.assertNotEqual(paciente.telefono, '00000000')
        self.assertEqual(models.Medico.objects.order_by('pk').first().nombres, 'Roberto Estuardo')
        self.assertEqual(models.Enfermero.objects.order_by('pk').first().nombres, 'Lucía Maribel')
        self.assertIn('Jacarandás', models.Sede.objects.order_by('pk').first().nombre)
        campos_presentados = {
            models.Sede: ('nombre', 'direccion', 'municipio', 'departamento', 'telefono'),
            models.Aseguradora: ('nombre', 'direccion', 'correo'),
            models.CondicionCronica: ('nombre', 'descripcion'),
            models.Especialidad: ('nombre', 'descripcion'),
            models.ComponenteActivo: ('nombre',),
            models.Medicamento: ('nombre_comercial', 'forma_farmaceutica', 'concentracion'),
            models.CatalogoExamen: ('nombre',), models.Procedimiento: ('nombre',),
            models.DiagnosticoCIE10: ('descripcion',),
            Cita: ('motivo_consulta',), Triaje: ('observaciones',),
            Consulta: ('anamnesis', 'examen_fisico', 'plan_tratamiento'),
            models.DetalleReceta: ('dosis', 'via_administracion'),
            models.OrdenExamen: ('resultado',), DetalleFactura: ('descripcion',),
            models.AlergiaPaciente: ('reaccion',),
        }
        for modelo, campos in campos_presentados.items():
            for fila in modelo.objects.values(*campos):
                for campo, valor in fila.items():
                    with self.subTest(tabla=modelo._meta.db_table, campo=campo):
                        self.assertTrue(valor)
                        self.assertNotRegex(valor.lower(), r'prueba|fictici|simulad|demostraci|^00000000$')
        with connection.cursor() as cursor:
            cursor.execute('SELECT observaciones FROM PACIENTE_CONDICION')
            for (observacion,) in cursor.fetchall():
                self.assertTrue(observacion)
                self.assertNotIn('Relación ficticia de prueba.', observacion)

    def test_naturalizar_textos_anteriores_preserva_filas_claves_fechas_e_importes(self):
        self.cargar()
        paciente, cita, sede = self.preparar_textos_anteriores()
        antes = self.estado_protegido()
        self.cargar(naturalizar=True)
        self.assertEqual(self.estado_protegido(), antes)
        paciente.refresh_from_db()
        cita.refresh_from_db()
        sede.refresh_from_db()
        self.assertEqual(paciente.nombres, 'Ana Lucía')
        self.assertEqual(paciente.apellidos, 'Morales Castillo')
        self.assertNotIn('cita de prueba', cita.motivo_consulta)
        self.assertIn('Jacarandás', sede.nombre)
        consulta = Consulta.objects.get(id_cita=cita)
        self.assertNotIn('historia de prueba', consulta.anamnesis)
        self.assertNotIn('simulado', consulta.examen_fisico)
        self.assertNotIn('ficticio', consulta.plan_tratamiento)
        self.assertNotIn('ficticio', Triaje.objects.get(id_cita=cita).observaciones)
        for descripcion in DetalleFactura.objects.values_list('descripcion', flat=True):
            self.assertNotIn('de prueba', descripcion)
        with connection.cursor() as cursor:
            cursor.execute('SELECT observaciones FROM PACIENTE_CONDICION WHERE id_paciente = %s',
                           [paciente.pk])
            for (observacion,) in cursor.fetchall():
                self.assertNotIn('Relación ficticia de prueba.', observacion)
        natural = self.estado()
        self.cargar(naturalizar=True)
        self.cargar()
        self.assertEqual(self.estado(), natural)

    def test_naturalizar_conserva_ediciones_manuales_y_lotes_ajenos(self):
        self.cargar()
        paciente, cita, sede = self.preparar_textos_anteriores()
        self.cargar(lote='OTRO20261030')
        otro_paciente = Paciente.objects.get(num_expediente='OTRO20261030-001')
        Paciente.objects.filter(pk=otro_paciente.pk).update(nombres='Paciente de prueba 001')
        ajeno_antes = Paciente.objects.values().get(pk=otro_paciente.pk)
        Paciente.objects.filter(pk=paciente.pk).update(nombres='Ana Patricia', telefono='1234-5678')
        Cita.objects.filter(pk=cita.pk).update(motivo_consulta='Revisión registrada manualmente')
        Consulta.objects.filter(id_cita=cita).update(anamnesis='Anotación conservada por el usuario')
        models.Sede.objects.filter(pk=sede.pk).update(direccion='Dirección corregida por el usuario')
        self.cargar(naturalizar=True)
        paciente.refresh_from_db()
        cita.refresh_from_db()
        sede.refresh_from_db()
        self.assertEqual(paciente.nombres, 'Ana Patricia')
        self.assertEqual(paciente.telefono, '1234-5678')
        self.assertEqual(paciente.apellidos, 'Morales Castillo')
        self.assertEqual(cita.motivo_consulta, 'Revisión registrada manualmente')
        self.assertEqual(Consulta.objects.get(id_cita=cita).anamnesis, 'Anotación conservada por el usuario')
        self.assertEqual(sede.direccion, 'Dirección corregida por el usuario')
        self.assertEqual(Paciente.objects.values().get(pk=otro_paciente.pk), ajeno_antes)

    def test_simular_naturalizacion_revierte_los_cambios(self):
        self.cargar()
        self.preparar_textos_anteriores()
        antes = self.estado()
        self.cargar(naturalizar=True, dry_run=True)
        self.assertEqual(self.estado(), antes)

    def test_naturalizar_resuelve_nombres_ocupados_sin_modificar_catalogos_ajenos(self):
        self.cargar()
        _, _, sede = self.preparar_textos_anteriores()
        sede_ajena = models.Sede.objects.create(
            nombre='Clínica Los Jacarandás', tipo='Clinica', direccion='Dirección de un registro ajeno',
        )
        componente_ajeno = models.ComponenteActivo.objects.create(nombre='Omeprazol')
        sede_antes = models.Sede.objects.values().get(pk=sede_ajena.pk)
        componente_antes = models.ComponenteActivo.objects.values().get(pk=componente_ajeno.pk)
        protegido = self.estado_protegido()
        self.cargar(naturalizar=True)
        sede.refresh_from_db()
        self.assertEqual(sede.nombre, 'Clínica Los Jacarandás (DEMO-20261030)')
        self.assertEqual(models.Sede.objects.values().get(pk=sede_ajena.pk), sede_antes)
        self.assertEqual(models.ComponenteActivo.objects.values().get(pk=componente_ajeno.pk), componente_antes)
        self.assertTrue(models.ComponenteActivo.objects.filter(nombre='Omeprazol (DEMO-20261030)').exists())
        self.assertEqual(self.estado_protegido(), protegido)
        natural = self.estado()
        self.cargar(naturalizar=True)
        self.cargar()
        self.assertEqual(self.estado(), natural)

    def test_naturalizar_un_lote_incompleto_no_crea_filas_y_revierte_cambios(self):
        self.cargar()
        self.preparar_textos_anteriores()
        antes = self.estado()
        with self.assertRaises(CommandError):
            self.cargar(naturalizar=True, pacientes=3)
        self.assertEqual(self.estado(), antes)

    def test_carga_crea_historial_relaciones_y_facturas_coherentes(self):
        self.cargar()
        self.assertEqual(Paciente.objects.count(), 2)
        self.assertEqual(Poliza.objects.count(), 2)
        self.assertEqual(Cita.objects.count(), 4)
        self.assertEqual(Consulta.objects.count(), 4)
        self.assertEqual(Triaje.objects.count(), 4)
        self.assertEqual(Factura.objects.count(), 4)
        self.assertGreaterEqual(DetalleFactura.objects.count(), 8)
        self.assertEqual(Pago.objects.count(), 4)
        for paciente in Paciente.objects.all():
            self.assertTrue(paciente.num_expediente.startswith('DEMO-20261030-'))
            self.assertRegex(paciente.dpi, r'^0[0-9]{12}$')
        for factura in Factura.objects.select_related('id_poliza', 'id_consulta__id_cita'):
            suma = sum(
                DetalleFactura.objects.filter(id_factura=factura).values_list('subtotal_linea', flat=True),
                Decimal('0.00'),
            )
            self.assertEqual(factura.subtotal, suma)
            self.assertEqual(factura.subtotal, factura.monto_paciente + factura.monto_aseguradora)
            self.assertEqual(factura.id_poliza.id_paciente_id, factura.id_consulta.id_cita.id_paciente_id)
        with connection.cursor() as cursor:
            for relacion in RELACIONES.values():
                cursor.execute('SELECT COUNT(*) FROM ' + relacion['tabla'])
                self.assertGreater(cursor.fetchone()[0], 0)

    def test_repetir_carga_no_duplica_ni_modifica_los_datos(self):
        self.cargar()
        antes = self.estado()
        self.cargar()
        self.assertEqual(self.estado(), antes)

    def test_lote_maximo_y_visita_sin_poliza_respetan_importes_y_longitudes(self):
        lote = 'ABCDEFGHIJKLMNO'
        self.assertEqual(len(lote), 15)
        self.cargar(lote=lote, pacientes=4)
        self.assertEqual(Paciente.objects.count(), 4)
        self.assertEqual(Factura.objects.count(), 8)
        facturas_sin_poliza = Factura.objects.filter(id_poliza__isnull=True)
        self.assertEqual(facturas_sin_poliza.count(), 1)
        factura = facturas_sin_poliza.get()
        self.assertEqual(factura.monto_aseguradora, Decimal('0.00'))
        self.assertEqual(factura.deducible_aplicado, Decimal('0.00'))
        self.assertEqual(factura.monto_paciente, factura.subtotal)
        self.assertGreater(factura.subtotal, Decimal('0.00'))
        self.assertEqual(max(map(len, Factura.objects.values_list('numero_factura', flat=True))), 20)
        self.assertLessEqual(max(map(len, Paciente.objects.values_list('num_expediente', flat=True))), 20)

    def test_lotes_distintos_no_colisionan_y_conservan_las_filas_anteriores(self):
        self.cargar()
        antes = self.estado()
        self.cargar(lote='OTRO20261030')
        despues = self.estado()
        self.assertEqual(Paciente.objects.count(), 4)
        self.assertEqual(len(set(Paciente.objects.values_list('dpi', flat=True))), 4)
        self.assertEqual(Factura.objects.count(), 8)
        self.assertEqual(len(set(Factura.objects.values_list('numero_factura', flat=True))), 8)
        for tabla, filas in antes.items():
            for fila in filas:
                with self.subTest(tabla=tabla):
                    self.assertIn(fila, despues[tabla])

    def test_conserva_los_registros_ajenos_al_lote(self):
        existente = Paciente.objects.create(
            num_expediente='EXISTENTE-001', dpi='9999999999999', nombres='Registro existente',
            apellidos='Sin cambios', fecha_nacimiento=date(1980, 1, 1), sexo='F',
            contacto_emergencia_nombre='Contacto existente', contacto_emergencia_telefono='00000000',
        )
        antes = Paciente.objects.values().get(pk=existente.pk)
        self.cargar()
        self.assertEqual(Paciente.objects.values().get(pk=existente.pk), antes)
        self.assertEqual(Paciente.objects.count(), 3)

    def test_un_error_revierte_toda_la_carga(self):
        antes = self.estado()
        with patch.object(Factura, 'save', side_effect=RuntimeError('Fallo de prueba')):
            with self.assertRaises((CommandError, RuntimeError)):
                self.cargar()
        self.assertEqual(self.estado(), antes)

    def test_simulacion_no_persiste_registros(self):
        antes = self.estado()
        self.cargar(dry_run=True)
        self.assertEqual(self.estado(), antes)

    def test_opciones_invalidas_no_crean_datos(self):
        antes = self.estado()
        for opciones in ({'pacientes': 0}, {'pacientes': 101}, {'lote': 'lote con espacios'}):
            with self.subTest(opciones=opciones), self.assertRaises(CommandError):
                self.cargar(**opciones)
        self.assertEqual(self.estado(), antes)
