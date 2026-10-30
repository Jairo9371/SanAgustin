"""Regresiones de plantillas, búsqueda y formatos, sin acceso a SQL Server."""
from datetime import datetime, time
from pathlib import Path

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.sql.where import WhereNode
from django.template import engines
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase

from .forms import formulario_para
from .models import Cita, Consulta, DiagnosticoCIE10, Turno
from .views import ListadoView, errores_de_guardado


class InterfazTest(SimpleTestCase):
    def test_todas_las_plantillas_compilan(self):
        directorio = Path(settings.BASE_DIR) / 'templates'
        for archivo in directorio.rglob('*.html'):
            nombre = archivo.relative_to(directorio).as_posix()
            with self.subTest(plantilla=nombre):
                engines['django'].get_template(nombre)

    def test_detalle_muestra_texto_completo_y_escapa_html(self):
        nota = ('Historia clínica extensa. ' * 40) + '\n<script>alert("x")</script>'
        consulta = Consulta(id_consulta=1, anamnesis=nota)
        html = render_to_string('gestion/detalle.html', {
            'titulo': 'Consultas médicas',
            'slug': 'consulta',
            'registro': consulta,
            'campos': [Consulta._meta.get_field('anamnesis')],
        })
        self.assertIn('Historia clínica extensa. ' * 40, html)
        self.assertIn('<br>', html)
        self.assertIn('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;', html)
        self.assertNotIn('<script>', html)

    def test_busqueda_incluye_codigo_cie10(self):
        vista = ListadoView()
        vista.model = DiagnosticoCIE10
        vista.request = RequestFactory().get('/tablas/diagnostico_cie10/', {'q': 'J06.9'})
        queryset = vista.get_queryset()

        def condiciones(nodo):
            for hijo in nodo.children:
                if isinstance(hijo, WhereNode):
                    yield from condiciones(hijo)
                else:
                    yield hijo

        filtros = list(condiciones(queryset.query.where))
        self.assertTrue(any(
            filtro.lhs.target.name == 'codigo_cie10'
            and filtro.lookup_name == 'icontains'
            and filtro.rhs == 'J06.9'
            for filtro in filtros
        ))


class PrecisionHorariosTest(SimpleTestCase):
    def test_fecha_hora_conserva_segundos_y_microsegundos_al_editar(self):
        fecha = datetime(2026, 10, 26, 8, 30, 45, 123456)
        formulario = formulario_para(Cita)(instance=Cita(
            id_cita=1, fecha_hora_programada=fecha,
        ))
        campo = formulario['fecha_hora_programada']
        valor_renderizado = campo.field.widget.format_value(campo.value())
        self.assertEqual(campo.field.clean(valor_renderizado), fecha)

    def test_hora_conserva_segundos_y_microsegundos_al_editar(self):
        hora = time(8, 30, 45, 123456)
        formulario = formulario_para(Turno)(instance=Turno(
            id_turno=1, hora_inicio=hora, hora_fin=time(12, 0),
        ))
        campo = formulario['hora_inicio']
        valor_renderizado = campo.field.widget.format_value(campo.value())
        self.assertEqual(campo.field.clean(valor_renderizado), hora)


class ErroresGuardadoTest(SimpleTestCase):
    class Formulario(forms.Form):
        cantidad = forms.IntegerField()

    def test_errores_de_campos_calculados_se_muestran_en_formulario(self):
        formulario = self.Formulario(data={'cantidad': '2'})
        self.assertTrue(formulario.is_valid())
        errores_de_guardado(formulario, ValidationError({
            'cantidad': 'Cantidad inválida.',
            'subtotal_linea': 'El subtotal calculado excede el máximo.',
        }))
        self.assertEqual(formulario.errors['cantidad'], ['Cantidad inválida.'])
        self.assertEqual(formulario.non_field_errors(), [
            'El subtotal calculado excede el máximo.',
        ])

    def test_errores_generales_de_guardado_se_muestran_en_formulario(self):
        formulario = self.Formulario(data={'cantidad': '2'})
        self.assertTrue(formulario.is_valid())
        errores_de_guardado(formulario, ValidationError('La factura ya cambió.'))
        self.assertEqual(formulario.non_field_errors(), ['La factura ya cambió.'])
