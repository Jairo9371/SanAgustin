"""Historial por paciente: consultas de lectura aisladas de SQL Server."""
from datetime import date, datetime, timedelta
from decimal import Decimal
import re
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from . import models
from .catalogo import MODELOS, RELACIONES
from .datos_prueba import cargar_datos_prueba
from .test_datos_prueba import TABLAS_PUENTE


@skipUnless(connection.vendor == 'sqlite', 'Usa --settings=hospital.test_settings para las pruebas aisladas.')
class HistorialPacienteTest(TransactionTestCase):
    databases = {'default'} if connection.vendor == 'sqlite' else set()

    def setUp(self):
        super().setUp()
        with connection.schema_editor() as editor:
            for modelo in MODELOS.values():
                editor.create_model(modelo)
        with connection.cursor() as cursor:
            for sentencia in TABLAS_PUENTE:
                cursor.execute(sentencia)
        cargar_datos_prueba(lote='HISTORIAL', pacientes=2)
        self.paciente = models.Paciente.objects.get(num_expediente='HISTORIAL-001')
        self.otro = models.Paciente.objects.get(num_expediente='HISTORIAL-002')
        self.staff = get_user_model().objects.create_user(username='personal_historial', is_staff=True)
        self.client.force_login(self.staff)
        self.url = reverse('gestion:consulta_historial')

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

    def buscar(self, paciente=None, **parametros):
        datos = {'dpi': (paciente or self.paciente).dpi}
        datos.update(parametros)
        return self.client.get(self.url, datos)

    def assert_sin_consultas_clinicas(self, consultas):
        tablas = [modelo._meta.db_table for modelo in MODELOS.values()]
        tablas.extend(relacion['tabla'] for relacion in RELACIONES.values())
        patron = re.compile(r'\b(?:FROM|JOIN)\s+[\["]?(?:' + '|'.join(tablas) + r')\b', re.IGNORECASE)
        self.assertFalse([consulta['sql'] for consulta in consultas if patron.search(consulta['sql'])])

    def crear_paciente_sin_historial(self):
        return models.Paciente.objects.create(
            num_expediente='HISTORIAL-VACIO', dpi='9999999999998',
            nombres='Beatriz', apellidos='Alvarado', fecha_nacimiento=date(1990, 5, 6), sexo='F',
            contacto_emergencia_nombre='Marta Alvarado', contacto_emergencia_telefono='5550-1234',
        )

    def crear_consulta(self, paciente, fecha, nota='Control registrado en el expediente'):
        ejemplo = models.Cita.objects.order_by('pk').first()
        cita = models.Cita.objects.create(
            id_paciente=paciente, id_medico=ejemplo.id_medico,
            id_consultorio=ejemplo.id_consultorio, fecha_hora_programada=fecha,
            canal_reserva='Presencial', motivo_consulta='Consulta de seguimiento', estado='Atendida',
        )
        return models.Consulta.objects.create(
            id_cita=cita, fecha_hora_consulta=fecha + timedelta(minutes=15), anamnesis=nota,
        )

    def test_solicita_login_y_rechaza_cuentas_sin_acceso_clinico(self):
        self.client.logout()
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.buscar()
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)
        self.assert_sin_consultas_clinicas(consultas)

        usuario = get_user_model().objects.create_user(username='sin_acceso_historial')
        self.client.force_login(usuario)
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.buscar()
        self.assertEqual(respuesta.status_code, 403)
        self.assert_sin_consultas_clinicas(consultas)
        self.assertNotContains(respuesta, self.paciente.dpi, status_code=403)

    def test_pantalla_inicial_no_carga_ni_muestra_expedientes(self):
        with CaptureQueriesContext(connection) as consultas:
            respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context['busqueda_realizada'])
        self.assertFalse(respuesta.context['form'].is_bound)
        self.assertIsNone(respuesta.context['paciente'])
        self.assertFalse(respuesta.context['historial'])
        self.assertNotContains(respuesta, self.paciente.dpi)
        self.assertNotContains(respuesta, self.paciente.nombres)
        self.assert_sin_consultas_clinicas(consultas)

    def test_dpi_invalido_no_ejecuta_consultas_clinicas(self):
        for dpi in ('', '123456789012', '12345678901234', "' OR 1=1--", '١' * 13):
            with self.subTest(dpi=dpi), CaptureQueriesContext(connection) as consultas:
                respuesta = self.client.get(self.url, {'dpi': dpi})
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn('dpi', respuesta.context['form'].errors)
            self.assertIsNone(respuesta.context['paciente'])
            self.assertFalse(respuesta.context['historial'])
            self.assert_sin_consultas_clinicas(consultas)

    def test_dpi_sin_coincidencia_no_muestra_otro_paciente(self):
        respuesta = self.client.get(self.url, {'dpi': '9999999999999'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['busqueda_realizada'])
        self.assertFalse(respuesta.context['form'].errors)
        self.assertIsNone(respuesta.context['paciente'])
        self.assertFalse(respuesta.context['historial'])
        self.assertNotContains(respuesta, self.paciente.nombres)
        self.assertNotContains(respuesta, self.otro.nombres)

    def test_acepta_espacios_exteriores_sin_perder_ceros_del_dpi(self):
        respuesta = self.client.get(self.url, {'dpi': '  ' + self.paciente.dpi + '  '})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['paciente'].pk, self.paciente.pk)
        self.assertEqual(respuesta.context['form'].cleaned_data['dpi'], self.paciente.dpi)

    def test_historial_reune_el_expediente_sin_duplicar_consultas(self):
        consulta = models.Consulta.objects.filter(id_cita__id_paciente=self.paciente).order_by('-fecha_hora_consulta').first()
        secundario = models.DiagnosticoCIE10.objects.create(codigo_cie10='HISTSEC', descripcion='Diagnóstico secundario de seguimiento')
        receta = models.Receta.objects.get(id_consulta=consulta)
        medicamento = models.Medicamento.objects.exclude(detallereceta__id_receta=receta).first()
        models.DetalleReceta.objects.create(
            id_receta=receta, id_medicamento=medicamento, dosis='Según receta archivada',
            via_administracion='Oral', frecuencia_horas=12, duracion_dias=5, cantidad_despachar=10,
        )
        examen = models.CatalogoExamen.objects.exclude(ordenexamen__id_consulta=consulta).first()
        models.OrdenExamen.objects.create(id_consulta=consulta, id_examen=examen,
            estado='Completado', resultado='Resultado adicional de laboratorio')
        procedimiento = models.Procedimiento.objects.create(nombre='Evaluación complementaria', precio=Decimal('25.00'))
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO CONSULTA_DIAGNOSTICO (id_consulta, codigo_cie10, tipo) VALUES (%s, %s, %s)',
                           [consulta.pk, secundario.pk, 'Secundario'])
            cursor.execute('INSERT INTO CONSULTA_PROCEDIMIENTO (id_consulta, id_procedimiento, cantidad) VALUES (%s, %s, %s)',
                           [consulta.pk, procedimiento.pk, 2])

        respuesta = self.buscar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['paciente'].pk, self.paciente.pk)
        historial = respuesta.context['historial']
        self.assertEqual(len(historial), 2)
        self.assertEqual(len({atencion['consulta'].pk for atencion in historial}), 2)
        fechas = [atencion['consulta'].fecha_hora_consulta for atencion in historial]
        self.assertEqual(fechas, sorted(fechas, reverse=True))
        reciente = historial[0]
        self.assertEqual(reciente['consulta'].pk, consulta.pk)
        self.assertEqual(len(reciente['diagnosticos']), 2)
        self.assertIn('HISTSEC', {diagnostico['codigo_cie10'] for diagnostico in reciente['diagnosticos']})
        self.assertEqual(len(reciente['medicamentos']), 2)
        self.assertEqual(len(reciente['examenes']), 2)
        self.assertEqual(len(reciente['procedimientos']), 2)
        self.assertIsNotNone(reciente['triaje'])
        self.assertIsNotNone(reciente['receta'])
        self.assertTrue(respuesta.context['condiciones'])
        self.assertTrue(respuesta.context['alergias'])
        for texto in (self.paciente.nombres, self.paciente.apellidos, secundario.descripcion,
                      medicamento.nombre_comercial, examen.nombre, procedimiento.nombre,
                      'Resultado adicional de laboratorio', consulta.anamnesis):
            self.assertContains(respuesta, texto)

    def test_excluye_datos_clinicos_y_personales_del_otro_paciente(self):
        models.Consulta.objects.filter(id_cita__id_paciente=self.otro).update(anamnesis='Historia exclusiva del otro paciente')
        models.AlergiaPaciente.objects.filter(id_paciente=self.otro).update(reaccion='Reacción exclusiva del otro paciente')
        respuesta = self.buscar()
        self.assertEqual(respuesta.status_code, 200)
        for atencion in respuesta.context['historial']:
            self.assertEqual(atencion['consulta'].id_cita.id_paciente_id, self.paciente.pk)
        for alergia in respuesta.context['alergias']:
            self.assertEqual(alergia.id_paciente_id, self.paciente.pk)
        for texto in (self.otro.nombres, self.otro.apellidos, self.otro.dpi,
                      'Historia exclusiva del otro paciente', 'Reacción exclusiva del otro paciente'):
            self.assertNotContains(respuesta, texto)

    def test_paciente_sin_consultas_no_convierte_citas_pendientes_en_atenciones(self):
        paciente = self.crear_paciente_sin_historial()
        ejemplo = models.Cita.objects.order_by('pk').first()
        models.Cita.objects.create(
            id_paciente=paciente, id_medico=ejemplo.id_medico, id_consultorio=ejemplo.id_consultorio,
            fecha_hora_programada=datetime(2026, 11, 10, 9), canal_reserva='Presencial',
            motivo_consulta='Cita todavía sin consulta', estado='Programada',
        )
        respuesta = self.buscar(paciente)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['paciente'].pk, paciente.pk)
        self.assertFalse(respuesta.context['historial'])
        self.assertEqual(respuesta.context['page_obj'].paginator.count, 0)
        self.assertContains(respuesta, paciente.nombres)

    def test_consulta_sin_diagnostico_triaje_receta_ni_examenes_se_conserva(self):
        paciente = self.crear_paciente_sin_historial()
        consulta = self.crear_consulta(paciente, datetime(2026, 10, 31, 9), 'Primera atención sin estudios complementarios')
        respuesta = self.buscar(paciente)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context['historial']), 1)
        atencion = respuesta.context['historial'][0]
        self.assertEqual(atencion['consulta'].pk, consulta.pk)
        self.assertIsNone(atencion['triaje'])
        self.assertIsNone(atencion['receta'])
        for campo in ('diagnosticos', 'medicamentos', 'examenes', 'procedimientos'):
            self.assertFalse(atencion[campo])
        self.assertContains(respuesta, consulta.anamnesis)

    def test_paginacion_conserva_paciente_y_orden_cronologico(self):
        for indice in range(9):
            self.crear_consulta(self.paciente, datetime(2026, 11, 1, 9) + timedelta(days=indice))
        primera = self.buscar()
        segunda = self.buscar(page=2)
        self.assertEqual(primera.status_code, 200)
        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(primera.context['page_obj'].paginator.count, 11)
        self.assertEqual(len(primera.context['historial']), 10)
        self.assertEqual(len(segunda.context['historial']), 1)
        todas = list(primera.context['historial']) + list(segunda.context['historial'])
        self.assertEqual(len({atencion['consulta'].pk for atencion in todas}), 11)
        self.assertTrue(all(atencion['consulta'].id_cita.id_paciente_id == self.paciente.pk for atencion in todas))
        fechas = [atencion['consulta'].fecha_hora_consulta for atencion in todas]
        self.assertEqual(fechas, sorted(fechas, reverse=True))
        self.assertContains(primera, 'dpi=' + self.paciente.dpi)
        self.assertContains(primera, 'page=2')
        self.assertContains(segunda, 'page=1')

    def test_textos_clinicos_se_muestran_completos_y_escapados(self):
        nota = 'Anotación extensa del expediente. ' * 40 + '\n<script>alert("historial")</script>'
        consulta = models.Consulta.objects.filter(id_cita__id_paciente=self.paciente).first()
        models.Consulta.objects.filter(pk=consulta.pk).update(anamnesis=nota)
        respuesta = self.buscar()
        self.assertContains(respuesta, 'Anotación extensa del expediente. ' * 40)
        self.assertContains(respuesta, '&lt;script&gt;alert(&quot;historial&quot;)&lt;/script&gt;')
        self.assertNotContains(respuesta, '<script>')
        self.assertContains(respuesta, '<br>')

    def test_respuesta_clinica_impide_almacenamiento_en_cache(self):
        respuesta = self.buscar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('private', respuesta.headers.get('Cache-Control', ''))
        self.assertIn('no-store', respuesta.headers.get('Cache-Control', ''))
