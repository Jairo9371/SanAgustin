from django.test import SimpleTestCase
from .catalogo import MODELOS, RELACIONES, SECCIONES

class EstructuraTest(SimpleTestCase):
    def test_todas_las_tablas_registradas(self):
        self.assertEqual(len(MODELOS), 25)
        self.assertEqual(len(RELACIONES), 5)
        self.assertEqual(sum(len(g['modulos']) for g in SECCIONES), 30)
    def test_modelos_no_gestionados(self):
        for slug, modelo in MODELOS.items():
            with self.subTest(slug=slug):
                self.assertFalse(modelo._meta.managed)
    def test_llaves_primarias(self):
        self.assertEqual(MODELOS['paciente']._meta.pk.column,'id_paciente')
        self.assertEqual(MODELOS['diagnostico_cie10']._meta.pk.column,'codigo_cie10')


class RelacionSchemaTest(SimpleTestCase):
    def test_las_cinco_relaciones_tienen_pk_doble(self):
        from .relaciones_crud import CAMPOS_RELACION, columnas_pk, comillas
        self.assertEqual(set(CAMPOS_RELACION), set(RELACIONES))
        for slug, config in RELACIONES.items():
            with self.subTest(tabla=slug):
                self.assertEqual(len(columnas_pk(slug)), 2)
                self.assertEqual(set(config['columnas']), set(CAMPOS_RELACION[slug]))
                self.assertTrue(config['tabla'].isupper())
        self.assertEqual(comillas('id_paciente'), '[id_paciente]')
        with self.assertRaises(ValueError):
            comillas('id_paciente]; DROP TABLE PACIENTE;--')

    def test_rutas_crud(self):
        from django.urls import reverse
        self.assertEqual(reverse('gestion:crear', args=['paciente']), '/tablas/paciente/nuevo/')
        self.assertEqual(reverse('gestion:editar', args=['paciente', '1']), '/tablas/paciente/1/editar/')
        self.assertEqual(reverse('gestion:nueva_relacion', args=['paciente_condicion']),
                         '/relaciones/paciente_condicion/nuevo/')
