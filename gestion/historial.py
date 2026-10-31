"""Lecturas del expediente clínico de un paciente, sin modificar sus registros."""
from collections import defaultdict

from django.core.paginator import Paginator
from django.db import connection

from .models import AlergiaPaciente, Consulta, DetalleReceta, OrdenExamen, Receta, Triaje


def _filas(sql, parametros):
    with connection.cursor() as cursor:
        cursor.execute(sql, parametros)
        columnas = [columna[0] for columna in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def consultar_historial(paciente, pagina=None):
    condiciones = _filas('''
        SELECT cc.nombre, pc.fecha_diagnostico, pc.observaciones
        FROM [PACIENTE_CONDICION] AS pc
        INNER JOIN [CONDICION_CRONICA] AS cc ON cc.id_condicion = pc.id_condicion
        WHERE pc.id_paciente = %s
        ORDER BY cc.nombre
    ''', [paciente.pk])
    alergias = list(AlergiaPaciente.objects.filter(id_paciente=paciente)
                    .select_related('id_componente').order_by('id_componente__nombre', 'pk'))
    consultas = (Consulta.objects.filter(id_cita__id_paciente=paciente)
                 .select_related('id_cita__id_medico__id_especialidad',
                                 'id_cita__id_consultorio__id_sede')
                 .order_by('-fecha_hora_consulta', '-pk'))
    paginator = Paginator(consultas, 10)
    page_obj = paginator.get_page(pagina)
    consultas_pagina = list(page_obj.object_list)
    atenciones = []
    if consultas_pagina:
        ids_consulta = [consulta.pk for consulta in consultas_pagina]
        ids_cita = [consulta.id_cita_id for consulta in consultas_pagina]
        triajes = {triaje.id_cita_id: triaje for triaje in
                   Triaje.objects.filter(id_cita_id__in=ids_cita).select_related('id_enfermero')}
        recetas = {receta.id_consulta_id: receta for receta in
                   Receta.objects.filter(id_consulta_id__in=ids_consulta)}
        medicamentos = defaultdict(list)
        for detalle in (DetalleReceta.objects.filter(id_receta_id__in=[r.pk for r in recetas.values()])
                        .select_related('id_medicamento').order_by('pk')):
            medicamentos[detalle.id_receta_id].append(detalle)
        examenes = defaultdict(list)
        for orden in (OrdenExamen.objects.filter(id_consulta_id__in=ids_consulta)
                      .select_related('id_examen').order_by('fecha_solicitud', 'pk')):
            examenes[orden.id_consulta_id].append(orden)

        # Las tablas puente tienen PK compuesta y no poseen modelos ORM.
        # Solo se interpolan marcadores; todos los valores se envían como parámetros.
        marcadores = ', '.join('%s' for _ in ids_consulta)
        diagnosticos = defaultdict(list)
        for diagnostico in _filas(f'''
            SELECT cd.id_consulta, cd.codigo_cie10, d.descripcion, cd.tipo
            FROM [CONSULTA_DIAGNOSTICO] AS cd
            INNER JOIN [DIAGNOSTICO_CIE10] AS d ON d.codigo_cie10 = cd.codigo_cie10
            WHERE cd.id_consulta IN ({marcadores})
            ORDER BY cd.id_consulta,
                     CASE WHEN cd.tipo = 'Principal' THEN 0 ELSE 1 END,
                     cd.codigo_cie10
        ''', ids_consulta):
            diagnosticos[diagnostico['id_consulta']].append(diagnostico)
        procedimientos = defaultdict(list)
        for procedimiento in _filas(f'''
            SELECT cp.id_consulta, p.nombre, cp.cantidad
            FROM [CONSULTA_PROCEDIMIENTO] AS cp
            INNER JOIN [PROCEDIMIENTO] AS p ON p.id_procedimiento = cp.id_procedimiento
            WHERE cp.id_consulta IN ({marcadores})
            ORDER BY cp.id_consulta, p.nombre
        ''', ids_consulta):
            procedimientos[procedimiento['id_consulta']].append(procedimiento)
        for consulta in consultas_pagina:
            receta = recetas.get(consulta.pk)
            atenciones.append({
                'consulta': consulta,
                'triaje': triajes.get(consulta.id_cita_id),
                'diagnosticos': diagnosticos[consulta.pk],
                'receta': receta,
                'medicamentos': medicamentos[receta.pk] if receta else [],
                'examenes': examenes[consulta.pk],
                'procedimientos': procedimientos[consulta.pk],
            })
    page_obj.object_list = atenciones
    return {
        'condiciones': condiciones, 'alergias': alergias, 'historial': atenciones,
        'page_obj': page_obj, 'paginator': paginator, 'is_paginated': paginator.num_pages > 1,
    }
