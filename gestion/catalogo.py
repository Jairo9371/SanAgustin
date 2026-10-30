"""Registro de módulos; solo las tablas conocidas se pueden consultar."""
from . import models

SECCIONES = [{'nombre': 'Pacientes y seguros', 'modulos': [{'slug': 'paciente', 'nombre': 'Pacientes', 'pk_compuesta': False}, {'slug': 'condicion_cronica', 'nombre': 'Condiciones crónicas', 'pk_compuesta': False}, {'slug': 'paciente_condicion', 'nombre': 'Condiciones por paciente', 'pk_compuesta': True}, {'slug': 'alergia_paciente', 'nombre': 'Alergias por paciente', 'pk_compuesta': False}, {'slug': 'aseguradora', 'nombre': 'Aseguradoras', 'pk_compuesta': False}, {'slug': 'poliza', 'nombre': 'Pólizas', 'pk_compuesta': False}]}, {'nombre': 'Personal y sedes', 'modulos': [{'slug': 'sede', 'nombre': 'Sedes', 'pk_compuesta': False}, {'slug': 'consultorio', 'nombre': 'Consultorios', 'pk_compuesta': False}, {'slug': 'especialidad', 'nombre': 'Especialidades', 'pk_compuesta': False}, {'slug': 'medico', 'nombre': 'Médicos', 'pk_compuesta': False}, {'slug': 'medico_subespecialidad', 'nombre': 'Subespecialidades médicas', 'pk_compuesta': True}, {'slug': 'turno', 'nombre': 'Turnos médicos', 'pk_compuesta': False}, {'slug': 'enfermero', 'nombre': 'Enfermeros', 'pk_compuesta': False}]}, {'nombre': 'Atención médica', 'modulos': [{'slug': 'cita', 'nombre': 'Citas', 'pk_compuesta': False}, {'slug': 'triaje', 'nombre': 'Triajes', 'pk_compuesta': False}, {'slug': 'diagnostico_cie10', 'nombre': 'Diagnósticos CIE-10', 'pk_compuesta': False}, {'slug': 'consulta', 'nombre': 'Consultas médicas', 'pk_compuesta': False}, {'slug': 'consulta_diagnostico', 'nombre': 'Diagnósticos por consulta', 'pk_compuesta': True}]}, {'nombre': 'Farmacia y recetas', 'modulos': [{'slug': 'componente_activo', 'nombre': 'Componentes activos', 'pk_compuesta': False}, {'slug': 'medicamento', 'nombre': 'Medicamentos', 'pk_compuesta': False}, {'slug': 'medicamento_componente', 'nombre': 'Componentes de medicamentos', 'pk_compuesta': True}, {'slug': 'receta', 'nombre': 'Recetas', 'pk_compuesta': False}, {'slug': 'detalle_receta', 'nombre': 'Detalles de receta', 'pk_compuesta': False}]}, {'nombre': 'Exámenes y procedimientos', 'modulos': [{'slug': 'catalogo_examen', 'nombre': 'Catálogo de exámenes', 'pk_compuesta': False}, {'slug': 'orden_examen', 'nombre': 'Órdenes de examen', 'pk_compuesta': False}, {'slug': 'procedimiento', 'nombre': 'Procedimientos', 'pk_compuesta': False}, {'slug': 'consulta_procedimiento', 'nombre': 'Procedimientos por consulta', 'pk_compuesta': True}]}, {'nombre': 'Facturación', 'modulos': [{'slug': 'factura', 'nombre': 'Facturas', 'pk_compuesta': False}, {'slug': 'detalle_factura', 'nombre': 'Detalles de factura', 'pk_compuesta': False}, {'slug': 'pago', 'nombre': 'Pagos', 'pk_compuesta': False}]}]

MODELOS = {
    'paciente': models.Paciente,
    'condicion_cronica': models.CondicionCronica,
    'aseguradora': models.Aseguradora,
    'poliza': models.Poliza,
    'sede': models.Sede,
    'consultorio': models.Consultorio,
    'especialidad': models.Especialidad,
    'medico': models.Medico,
    'turno': models.Turno,
    'enfermero': models.Enfermero,
    'cita': models.Cita,
    'triaje': models.Triaje,
    'diagnostico_cie10': models.DiagnosticoCIE10,
    'consulta': models.Consulta,
    'componente_activo': models.ComponenteActivo,
    'medicamento': models.Medicamento,
    'receta': models.Receta,
    'detalle_receta': models.DetalleReceta,
    'catalogo_examen': models.CatalogoExamen,
    'orden_examen': models.OrdenExamen,
    'procedimiento': models.Procedimiento,
    'factura': models.Factura,
    'detalle_factura': models.DetalleFactura,
    'pago': models.Pago,
    'alergia_paciente': models.AlergiaPaciente,
}

RELACIONES = {
    'paciente_condicion': {'tabla': 'PACIENTE_CONDICION', 'nombre': 'Condiciones por paciente', 'columnas': ['id_paciente', 'id_condicion', 'fecha_diagnostico', 'observaciones']},
    'medico_subespecialidad': {'tabla': 'MEDICO_SUBESPECIALIDAD', 'nombre': 'Subespecialidades médicas', 'columnas': ['id_medico', 'id_especialidad']},
    'consulta_diagnostico': {'tabla': 'CONSULTA_DIAGNOSTICO', 'nombre': 'Diagnósticos por consulta', 'columnas': ['id_consulta', 'codigo_cie10', 'tipo']},
    'medicamento_componente': {'tabla': 'MEDICAMENTO_COMPONENTE', 'nombre': 'Componentes de medicamentos', 'columnas': ['id_medicamento', 'id_componente']},
    'consulta_procedimiento': {'tabla': 'CONSULTA_PROCEDIMIENTO', 'nombre': 'Procedimientos por consulta', 'columnas': ['id_consulta', 'id_procedimiento', 'cantidad']},
}

ETIQUETAS = {m["slug"]: m["nombre"] for grupo in SECCIONES for m in grupo["modulos"]}
