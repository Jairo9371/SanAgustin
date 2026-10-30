"""Regresiones de relaciones sin acceder a las tablas SQL Server."""
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch, sentinel

from django.core.exceptions import ValidationError
from django.db import DataError
from django.http import Http404
from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase

from .relaciones_crud import (
    claves_relacion, crear_formulario, editar_relacion, eliminar_relacion,
    fila_relacion, nueva_relacion,
)
from .views import RelacionesView


class PaginacionRelacionesTest(SimpleTestCase):
    def contexto(self, total, pagina, filas, slug='paciente_condicion'):
        vista = RelacionesView()
        vista.setup(RequestFactory().get('/', {'page': pagina}))
        with patch('gestion.views.connection') as conexion:
            cursor = conexion.cursor.return_value.__enter__.return_value
            cursor.fetchone.return_value = (total,)
            cursor.fetchall.return_value = filas
            contexto = vista.get_context_data(slug=slug)
        return contexto, cursor

    def test_se_puede_navegar_mas_alla_de_cien_relaciones(self):
        filas = [(i, 1, None, None) for i in range(101, 126)]
        contexto, cursor = self.contexto(130, 5, filas)
        self.assertEqual(contexto['paginator'].num_pages, 6)
        self.assertEqual(contexto['page_obj'].number, 5)
        self.assertEqual(contexto['filas'], filas)
        self.assertTrue(contexto['page_obj'].has_next())
        consulta, parametros = cursor.execute.call_args.args
        self.assertIn('ORDER BY [id_paciente], [id_condicion]', consulta)
        self.assertIn('OFFSET %s ROWS FETCH NEXT %s ROWS ONLY', consulta)
        self.assertEqual(parametros, [100, 25])
        html = get_template('gestion/relaciones.html').render(contexto)
        self.assertIn('?page=6', html)
        self.assertIn('Total de registros: 130', html)

    def test_componentes_paginan_con_nombres_y_claves_para_acciones(self):
        filas = [(26, 3, 'Medicamento de prueba', 'Componente de prueba')]
        contexto, cursor = self.contexto(26, 2, filas, slug='medicamento_componente')
        self.assertEqual(contexto['paginator'].count, 26)
        self.assertEqual(contexto['page_obj'].number, 2)
        self.assertEqual(contexto['page_obj'].object_list, filas)
        consulta, parametros = cursor.execute.call_args.args
        self.assertIn('INNER JOIN MEDICAMENTO AS m', consulta)
        self.assertIn('INNER JOIN COMPONENTE_ACTIVO AS ca', consulta)
        self.assertIn('ORDER BY mc.id_medicamento, mc.id_componente', consulta)
        self.assertIn('OFFSET %s ROWS FETCH NEXT %s ROWS ONLY', consulta)
        self.assertEqual(parametros, [25, 25])
        html = get_template('gestion/relaciones.html').render(contexto)
        self.assertIn('Medicamento de prueba', html)
        self.assertIn('Componente de prueba', html)
        self.assertIn('/relaciones/medicamento_componente/26/3/editar/', html)
        self.assertIn('/relaciones/medicamento_componente/26/3/eliminar/', html)
        self.assertIn('Total de registros: 26', html)

    def test_lista_vacia_y_pagina_final(self):
        vacio, _ = self.contexto(0, 1, [])
        self.assertFalse(vacio['is_paginated'])
        self.assertEqual(vacio['page_obj'].number, 1)
        self.assertIn('No hay registros.', get_template('gestion/relaciones.html').render(vacio))
        final, cursor = self.contexto(101, 5, [(101, 1, None, None)])
        self.assertFalse(final['page_obj'].has_next())
        self.assertEqual(cursor.execute.call_args.args[1], [100, 25])

    def test_pagina_invalida_es_404(self):
        for pagina in ('abc', '0', '-1', '7'):
            with self.subTest(pagina=pagina), self.assertRaises(Http404):
                self.contexto(130, pagina, [])


class ValidacionRelacionesTest(SimpleTestCase):
    def request(self, metodo='get'):
        request = getattr(RequestFactory(), metodo)('/')
        request.user = SimpleNamespace(is_authenticated=True, is_active=True, is_staff=True)
        return request

    def test_cantidad_respeta_el_rango_int_de_sql(self):
        campo = crear_formulario('consulta_procedimiento').fields['cantidad']
        self.assertEqual(campo.clean('2147483647'), 2147483647)
        for valor in ('0', '-1', '2147483648'):
            with self.subTest(valor=valor), self.assertRaises(ValidationError):
                campo.clean(valor)

    def test_claves_se_convierten_y_codigo_cie10_se_preserva(self):
        self.assertEqual(claves_relacion('paciente_condicion', '001', '2'), [1, 2])
        self.assertEqual(claves_relacion('consulta_diagnostico', '1', 'J06.9'), [1, 'J06.9'])

    def test_claves_invalidas_no_llegan_a_sql(self):
        with patch('gestion.relaciones_crud.connection') as conexion:
            casos = (
                ('paciente_condicion', 'abc', '1'),
                ('paciente_condicion', '2147483648', '1'),
                ('paciente_condicion', '-2147483649', '1'),
                ('consulta_diagnostico', '1', 'codigo-demasiado-largo'),
            )
            for slug, clave_1, clave_2 in casos:
                with self.subTest(slug=slug, clave_1=clave_1, clave_2=clave_2):
                    with self.assertRaises(Http404):
                        fila_relacion(slug, clave_1, clave_2)
            for vista in (editar_relacion, eliminar_relacion):
                with self.assertRaises(Http404):
                    vista(self.request(), 'paciente_condicion', 'abc', '1')
            conexion.cursor.assert_not_called()

    def test_consulta_de_fila_usa_claves_normalizadas(self):
        with patch('gestion.relaciones_crud.connection') as conexion:
            cursor = conexion.cursor.return_value.__enter__.return_value
            cursor.fetchone.return_value = (1, 2, None, None)
            fila = fila_relacion('paciente_condicion', '001', '002')
        self.assertEqual(cursor.execute.call_args.args[1], [1, 2])
        self.assertEqual(fila['id_paciente'], 1)

    def test_error_de_datos_se_presenta_en_el_formulario(self):
        formulario = Mock()
        formulario.cleaned_data = {'id_medico': 1, 'id_especialidad': 2}
        formulario.is_valid.return_value = True
        with patch('gestion.relaciones_crud.crear_formulario', return_value=formulario), \
                patch('gestion.relaciones_crud.transaction.atomic', return_value=nullcontext()), \
                patch('gestion.relaciones_crud.connection') as conexion, \
                patch('gestion.relaciones_crud.render', return_value=sentinel.respuesta):
            conexion.cursor.return_value.__enter__.return_value.execute.side_effect = DataError('fuera de rango')
            respuesta = nueva_relacion(self.request('post'), 'medico_subespecialidad')
        self.assertIs(respuesta, sentinel.respuesta)
        formulario.add_error.assert_called_once()
        self.assertEqual(formulario.add_error.call_args.args[0], None)

