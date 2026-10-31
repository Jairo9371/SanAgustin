"""Perfiles ficticios para los registros de demostración del hospital.

Los nombres y direcciones se construyen para este proyecto. Los correos usan
example.com y las claves que identifican el lote se conservan por separado.
"""
import unicodedata


SEDES = [
    {
        'nombre': 'Clínica Los Jacarandás', 'tipo': 'Clinica',
        'direccion': '12 avenida 8-46, zona 7, colonia Jardines del Norte',
        'municipio': 'Guatemala', 'departamento': 'Guatemala', 'telefono': '5550-4102',
    },
    {
        'nombre': 'Centro Médico Vista Hermosa', 'tipo': 'Centro medico',
        'direccion': '4a calle 6-18, zona 4, colonia El Encinal',
        'municipio': 'Mixco', 'departamento': 'Guatemala', 'telefono': '5550-5824',
    },
    {
        'nombre': 'Clínica Las Gardenias', 'tipo': 'Clinica',
        'direccion': '7a avenida 3-52, zona 1, barrio La Esperanza',
        'municipio': 'Villa Nueva', 'departamento': 'Guatemala', 'telefono': '5550-7361',
    },
]

ENFERMEROS = [
    {'nombres': 'Lucía Maribel', 'apellidos': 'Ortiz de León', 'telefono': '5550-1284'},
    {'nombres': 'Esteban Alejandro', 'apellidos': 'Castañeda Méndez', 'telefono': '5550-2437'},
    {'nombres': 'Rosa Gabriela', 'apellidos': 'Pineda Estrada', 'telefono': '5550-3569'},
]

MEDICOS = [
    {
        'nombres': 'Roberto Estuardo', 'apellidos': 'Mendoza Salazar',
        'telefono': '5550-4728', 'correo': 'roberto.mendoza@example.com',
    },
    {
        'nombres': 'Elena Patricia', 'apellidos': 'Santos Villagrán',
        'telefono': '5550-5942', 'correo': 'elena.santos@example.com',
    },
    {
        'nombres': 'Javier Alejandro', 'apellidos': 'Monterroso León',
        'telefono': '5550-6183', 'correo': 'javier.monterroso@example.com',
    },
    {
        'nombres': 'Mariana Isabel', 'apellidos': 'Cifuentes Bolaños',
        'telefono': '5550-8275', 'correo': 'mariana.cifuentes@example.com',
    },
]

ASEGURADORAS = [
    {
        'nombre': 'Seguros Valle Claro', 'telefono': '5550-1426',
        'correo': 'autorizaciones.valleclaro@example.com',
        'direccion': '8a avenida 5-24, zona 9, edificio Alameda, oficina 302',
    },
    {
        'nombre': 'Protección Médica del Bosque', 'telefono': '5550-2681',
        'correo': 'servicio.delbosque@example.com',
        'direccion': '3a calle 11-38, zona 10, edificio Los Cedros, oficina 201',
    },
    {
        'nombre': 'Previsión Integral del Altiplano', 'telefono': '5550-3947',
        'correo': 'coberturas.altiplano@example.com',
        'direccion': '6a avenida 2-16, zona 1, centro comercial La Plazuela, local 8',
    },
]

CONDICIONES = [
    {
        'nombre': 'Hipertensión arterial esencial',
        'descripcion': 'Antecedente de presión arterial elevada con seguimiento en consulta externa.',
    },
    {
        'nombre': 'Diabetes mellitus tipo 2',
        'descripcion': 'Antecedente de alteración de la glucosa documentado en controles previos.',
    },
    {
        'nombre': 'Rinitis alérgica persistente',
        'descripcion': 'Episodios recurrentes de congestión nasal y estornudos asociados a exposición ambiental.',
    },
]

EXAMENES = [
    {'nombre': 'Hematología completa', 'tipo': 'Laboratorio'},
    {'nombre': 'Glucosa en ayunas', 'tipo': 'Laboratorio'},
    {'nombre': 'Perfil lipídico', 'tipo': 'Laboratorio'},
]

PROCEDIMIENTOS = [
    {'nombre': 'Electrocardiograma en reposo'},
    {'nombre': 'Curación de herida superficial'},
    {'nombre': 'Nebulización en consulta externa'},
]

ESPECIALIDADES = [
    {
        'nombre': 'Medicina Familiar',
        'descripcion': 'Atención integral, evaluación inicial y seguimiento de pacientes en consulta externa.',
    },
    {
        'nombre': 'Medicina Interna',
        'descripcion': 'Evaluación de pacientes adultos y seguimiento de enfermedades crónicas.',
    },
    {
        'nombre': 'Cardiología',
        'descripcion': 'Evaluación del sistema cardiovascular y seguimiento de sus factores de riesgo.',
    },
    {
        'nombre': 'Dermatología',
        'descripcion': 'Evaluación de lesiones y afecciones de la piel, el cabello y las uñas.',
    },
]

COMPONENTES = [
    {'nombre': 'Omeprazol'},
    {'nombre': 'Loratadina'},
    {'nombre': 'Metformina'},
    {'nombre': 'Losartán potásico'},
    {'nombre': 'Atorvastatina'},
    {'nombre': 'Cetirizina'},
]

MEDICAMENTOS = [
    {'nombre_comercial': 'Gastrolev', 'forma_farmaceutica': 'Cápsula', 'concentracion': '20 mg'},
    {'nombre_comercial': 'Alernova', 'forma_farmaceutica': 'Tableta', 'concentracion': '10 mg'},
    {'nombre_comercial': 'Gluconor', 'forma_farmaceutica': 'Tableta', 'concentracion': '500 mg'},
    {'nombre_comercial': 'Presoval', 'forma_farmaceutica': 'Tableta', 'concentracion': '50 mg'},
    {'nombre_comercial': 'Lipraval', 'forma_farmaceutica': 'Tableta', 'concentracion': '20 mg'},
    {'nombre_comercial': 'Cetrivía', 'forma_farmaceutica': 'Tableta', 'concentracion': '10 mg'},
]

DIAGNOSTICOS = [
    {'descripcion': 'Cefalea de tipo tensional'},
    {'descripcion': 'Dispepsia funcional'},
    {'descripcion': 'Dermatitis de contacto'},
]

_PACIENTES = [
    ('Ana Lucía', 'Morales Castillo', 'Marta Elena Castillo', 'Madre'),
    ('José Andrés', 'Pérez Méndez', 'Isabel Cristina Méndez', 'Madre'),
    ('María Fernanda', 'López Ramírez', 'Andrés Estuardo López', 'Hermano'),
    ('Luis Fernando', 'García Escobar', 'Claudia Beatriz Escobar', 'Madre'),
    ('Andrea Sofía', 'Hernández Pineda', 'Teresa Isabel Pineda', 'Madre'),
    ('Carlos Eduardo', 'Castillo Reyes', 'Rosa María Reyes', 'Madre'),
    ('Daniela Paola', 'Méndez Cabrera', 'Sergio Antonio Méndez', 'Padre'),
    ('Miguel Ángel', 'Ramírez Solís', 'Elena Patricia Solís', 'Madre'),
    ('Sofía Alejandra', 'Reyes Castañeda', 'Luis Enrique Reyes', 'Hermano'),
    ('Juan Pablo', 'Vásquez Molina', 'Gabriela Isabel Molina', 'Madre'),
    ('Valeria Isabel', 'Cabrera Fuentes', 'Jorge Roberto Cabrera', 'Padre'),
    ('Diego Alejandro', 'Molina Arévalo', 'María Elena Arévalo', 'Madre'),
    ('Gabriela Fernanda', 'Escobar Soto', 'Marcos Antonio Escobar', 'Hermano'),
    ('Ricardo Antonio', 'Fuentes Aguilar', 'Silvia Carolina Aguilar', 'Madre'),
    ('María José', 'Arévalo Rivas', 'Ernesto Rafael Arévalo', 'Padre'),
    ('Óscar David', 'Soto Calderón', 'Ana Beatriz Calderón', 'Madre'),
    ('Camila Beatriz', 'Aguilar Marroquín', 'Patricia Lorena Marroquín', 'Madre'),
    ('Sergio Estuardo', 'Rivas Chacón', 'Héctor Manuel Rivas', 'Hermano'),
    ('Paola Vanessa', 'Calderón Alvarado', 'Gloria Estela Alvarado', 'Madre'),
    ('Jorge Alberto', 'Marroquín Estrada', 'Mónica Alejandra Estrada', 'Madre'),
]

_DIRECCIONES = [
    '6a avenida 14-28, zona 7, colonia Las Brisas, Guatemala',
    '3a calle 9-42, zona 4, colonia El Encinal, Mixco',
    '10 avenida 2-16, zona 1, barrio El Rosario, Villa Nueva',
    '5a calle 7-35, zona 6, colonia La Arboleda, Guatemala',
    '2a avenida 11-64, zona 3, colonia Los Álamos, Mixco',
    '8a calle 4-19, zona 2, barrio San Gabriel, Villa Nueva',
    '11 avenida 6-27, zona 5, colonia El Mirador, Guatemala',
    '4a calle 13-52, zona 7, colonia Valle del Sol, Mixco',
    '7a avenida 8-14, zona 1, barrio La Esperanza, Villa Nueva',
    '9a calle 3-46, zona 11, colonia Las Acacias, Guatemala',
    '1a avenida 10-38, zona 4, colonia Los Olivos, Mixco',
    '6a calle 5-71, zona 3, colonia El Porvenir, Villa Nueva',
    '12 avenida 9-25, zona 12, colonia La Alameda, Guatemala',
    '2a calle 8-63, zona 6, colonia Los Cipreses, Mixco',
    '5a avenida 12-17, zona 1, barrio San Rafael, Villa Nueva',
    '8a calle 7-49, zona 2, colonia Jardines de la Paz, Guatemala',
    '3a avenida 4-86, zona 5, colonia La Floresta, Mixco',
    '10 calle 6-32, zona 4, colonia Los Pinos, Villa Nueva',
    '7a avenida 15-24, zona 18, colonia Santa Elena, Guatemala',
    '4a calle 2-58, zona 8, colonia Monte Verde, Mixco',
]


def _correo(nombres, apellidos):
    texto = unicodedata.normalize('NFKD', nombres + ' ' + apellidos)
    texto = texto.encode('ascii', 'ignore').decode('ascii').lower()
    return '.'.join(texto.split()) + '@example.com'


def perfil_paciente(numero):
    """Devuelve hasta cien identidades distintas sin numerar los nombres."""
    if isinstance(numero, bool) or not isinstance(numero, int) or not 1 <= numero <= 100:
        raise ValueError('El número del paciente debe estar entre 1 y 100.')
    indice = (numero - 1) % len(_PACIENTES)
    grupo = (numero - 1) // len(_PACIENTES)
    nombres, apellidos, contacto, parentesco = _PACIENTES[indice]
    if grupo:
        segundo_apellido = ('Cifuentes', 'Sandoval', 'Rosales', 'Paz')[grupo - 1]
        apellidos = apellidos.split()[0] + ' ' + segundo_apellido
    return {
        'nombres': nombres, 'apellidos': apellidos,
        'direccion': _DIRECCIONES[indice], 'telefono': f'5550-{1000 + numero * 37:04}',
        'correo': _correo(nombres, apellidos),
        'contacto_emergencia_nombre': contacto,
        'contacto_emergencia_telefono': f'5551-{2000 + numero * 41:04}',
        'contacto_emergencia_parentesco': parentesco,
    }


_CONSULTAS = [
    {
        'motivos': ('Dolor de cabeza al finalizar la jornada laboral', 'Revisión por episodios de dolor de cabeza'),
        'anamnesis': (
            'Refiere dolor de cabeza intermitente desde hace tres días, principalmente al final de la tarde. '
            'Relaciona los episodios con jornadas prolongadas frente a la computadora.',
            'Acude a revisión. Refiere episodios de menor intensidad y ha retomado sus actividades habituales. '
            'Se revisan los antecedentes consignados en la consulta anterior.',
        ),
        'examen_fisico': 'Paciente orientado y colaborador. Marcha conservada, sin alteraciones evidentes durante la exploración.',
        'plan_tratamiento': 'Se registra la evolución de los síntomas y se acuerda seguimiento en consulta externa.',
    },
    {
        'motivos': ('Malestar abdominal después de las comidas', 'Control por molestias digestivas recurrentes'),
        'anamnesis': (
            'Refiere sensación de llenura y malestar en la parte alta del abdomen después de las comidas. '
            'Los síntomas han sido intermitentes durante las últimas dos semanas.',
            'Acude a control y refiere menos molestias desde la última visita. '
            'Se revisan la alimentación habitual y los antecedentes de síntomas digestivos.',
        ),
        'examen_fisico': 'Abdomen blando, sin distensión visible. El paciente permanece cómodo durante la evaluación.',
        'plan_tratamiento': 'Se revisa el registro de síntomas y se deja constancia de los estudios solicitados para la próxima visita.',
    },
    {
        'motivos': ('Picazón y enrojecimiento en ambos antebrazos', 'Revisión de lesiones en la piel de los brazos'),
        'anamnesis': (
            'Refiere picazón y enrojecimiento en ambos antebrazos después de cambiar el jabón de uso habitual. '
            'No recuerda episodios similares en los últimos meses.',
            'Acude para revisión de las lesiones. Refiere disminución de la picazón y no describe nuevas áreas afectadas. '
            'Se compara la evolución con la anotación de la visita anterior.',
        ),
        'examen_fisico': 'Áreas de enrojecimiento leve en ambos antebrazos, sin secreción ni lesiones abiertas a la inspección.',
        'plan_tratamiento': 'Se documenta el aspecto de las lesiones y se programa seguimiento para valorar su evolución.',
    },
]

_RESULTADOS = (
    'Hemoglobina 13.8 g/dL; leucocitos 6,800/mm3; plaquetas 248,000/mm3.',
    'Glucosa en ayunas: 96 mg/dL. Muestra recibida a las 08:15 horas.',
    'Colesterol total 182 mg/dL; HDL 52 mg/dL; LDL 108 mg/dL; triglicéridos 110 mg/dL.',
)

_OBSERVACIONES_TRIAJE = (
    'Ingresa por sus propios medios y permanece orientado durante la entrevista.',
    'Se encuentra acompañado por un familiar durante el registro de ingreso.',
    'Se registran los signos vitales antes de pasar a consulta.',
    'Paciente tranquilo y colaborador durante la valoración inicial.',
    'Refiere haber realizado sus actividades habituales antes de acudir a la cita.',
    'Permanece sentado en sala de espera, sin dificultad para comunicarse.',
)


def perfil_visita(numero, visita, indice_medico):
    """Textos de expediente, sin cambiar las fechas ni los valores clínicos."""
    indice = (numero + visita) % len(_CONSULTAS)
    consulta = _CONSULTAS[indice]
    seguimiento = int(bool(visita))
    condicion = CONDICIONES[(numero - 1) % len(CONDICIONES)]['nombre'].lower()
    return {
        'motivo_consulta': consulta['motivos'][seguimiento],
        'observaciones_triaje': _OBSERVACIONES_TRIAJE[(numero + visita + indice_medico) % len(_OBSERVACIONES_TRIAJE)],
        'anamnesis': consulta['anamnesis'][seguimiento],
        'examen_fisico': consulta['examen_fisico'],
        'plan_tratamiento': consulta['plan_tratamiento'],
        'resultado_examen': _RESULTADOS[indice],
        'observaciones_condicion': f'Antecedente de {condicion} referido durante la entrevista inicial.',
        'reaccion_alergia': 'Refiere aparición de ronchas y picazón después de su uso; antecedente consignado por un familiar.',
        'dosis': 'Según receta archivada', 'via_administracion': 'Oral',
    }
