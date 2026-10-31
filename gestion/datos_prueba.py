"""Carga reproducible de registros ficticios para las treinta tablas del hospital."""
from collections import Counter
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import re

from django.core.exceptions import ValidationError
from django.db import connection, transaction

from . import models
from .catalogo import RELACIONES
from . import perfiles_prueba as perfiles


FECHA_BASE = date(2026, 10, 30)
LOTE_PREDETERMINADO = 'DEMO-20261030'


def validar_opciones(*, lote, pacientes, fecha_base):
    if not isinstance(lote, str) or not re.fullmatch(r'[A-Z0-9][A-Z0-9-]{0,14}', lote):
        raise ValidationError('El lote debe tener entre 1 y 15 caracteres: mayúsculas, números o guiones.')
    if isinstance(pacientes, bool) or not isinstance(pacientes, int) or not 1 <= pacientes <= 100:
        raise ValidationError('La cantidad de pacientes debe estar entre 1 y 100.')
    if isinstance(fecha_base, str):
        try:
            fecha_base = date.fromisoformat(fecha_base)
        except ValueError as exc:
            raise ValidationError('La fecha base debe tener formato AAAA-MM-DD.') from exc
    if not isinstance(fecha_base, date) or isinstance(fecha_base, datetime):
        raise ValidationError('La fecha base debe tener formato AAAA-MM-DD.')
    if not date(2020, 1, 1) <= fecha_base <= date(2099, 12, 31):
        raise ValidationError('La fecha base debe estar entre 2020 y 2099.')
    return fecha_base


class CargaPrueba:
    def __init__(self, lote, pacientes, fecha_base):
        self.lote = lote
        self.pacientes = pacientes
        self.fecha_base = fecha_base
        self.huella = sha256(lote.encode('ascii')).hexdigest()[:8].upper()
        self.creados = Counter()
        self.existentes = Counter()
        self.actualizados = Counter()
        self._actualizados = set()
        self._inspeccionados = set()

    def registro(self, modelo, *, defaults=None, existente=None, **identidad):
        """Nunca actualizar un registro encontrado; validar solo las nuevas altas."""
        objeto = existente if existente is not None else modelo.objects.filter(**identidad).first()
        if objeto is not None:
            self.existentes[modelo._meta.db_table] += 1
            return objeto, False
        objeto = modelo(**(defaults or {}), **identidad)
        # Los campos calculados (subtotal de línea) deben existir antes de full_clean.
        objeto.clean()
        objeto.full_clean()
        objeto.save(force_insert=True)
        self.creados[modelo._meta.db_table] += 1
        return objeto, True

    def catalogo(self, modelo, anterior, perfil, *, campo='nombre', defaults=None, existente=None):
        """Reconocer nombres originales, personalizados y catálogos compartidos."""
        nombre = perfil[campo]
        if existente is None:
            for candidato in (anterior, f'{nombre} ({self.lote})', nombre):
                existente = modelo.objects.filter(**{campo: candidato}).first()
                if existente is not None:
                    break
        valores = {**(defaults or {}), **perfil}
        valores.pop(campo)
        return self.registro(modelo, existente=existente, defaults=valores, **{campo: nombre})[0]

    def factura_existente(self, numero, visita, paciente):
        codigo = f'{self.lote}-F{(numero - 1) * 2 + visita + 1:03}'
        factura = models.Factura.objects.select_related('id_consulta__id_cita').filter(numero_factura=codigo).first()
        if factura is not None and factura.id_consulta.id_cita.id_paciente_id != paciente.pk:
            raise ValidationError(f'La factura {codigo} no pertenece al paciente esperado; no se modificó el lote.')
        return codigo, factura

    def relacion(self, slug, **datos):
        item = RELACIONES[slug]
        tabla = '[' + item['tabla'] + ']'
        columnas = item['columnas']
        claves = columnas[:2]
        condicion = ' AND '.join(f'[{columna}] = %s' for columna in claves)
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT 1 FROM {tabla} WHERE {condicion}', [datos[col] for col in claves])
            if cursor.fetchone() is not None:
                self.existentes[item['tabla']] += 1
                return
            nombres = ', '.join(f'[{columna}]' for columna in columnas)
            marcadores = ', '.join('%s' for _ in columnas)
            cursor.execute(f'INSERT INTO {tabla} ({nombres}) VALUES ({marcadores})',
                           [datos[columna] for columna in columnas])
            self.creados[item['tabla']] += 1

    def catalogos(self):
        etiqueta = f'{self.lote} PRUEBA'
        self.sedes = []
        self.consultorios = []
        self.enfermeros = []
        self.aseguradoras = []
        self.condiciones = []
        self.examenes = []
        self.procedimientos = []
        for indice in range(3):
            enfermero_previo = models.Enfermero.objects.filter(num_colegiado=f'D{self.huella}E{indice + 1:02}').first()
            sede = self.catalogo(models.Sede, f'{etiqueta} sede {indice + 1}', perfiles.SEDES[indice],
                                 existente=enfermero_previo.id_sede if enfermero_previo is not None else None)
            self.sedes.append(sede)
            consultorio, _ = self.registro(models.Consultorio, id_sede=sede, numero='DEMO-01',
                                           defaults={'piso': '1'})
            self.consultorios.append(consultorio)
            enfermero, _ = self.registro(models.Enfermero, num_colegiado=f'D{self.huella}E{indice + 1:02}', defaults={
                **perfiles.ENFERMEROS[indice], 'id_sede': sede,
            })
            self.enfermeros.append(enfermero)
            nit = f'D{self.huella}A{indice + 1:02}'
            seguro = self.catalogo(models.Aseguradora, f'{etiqueta} seguro {indice + 1}', perfiles.ASEGURADORAS[indice],
                                   defaults={'nit': nit}, existente=models.Aseguradora.objects.filter(nit=nit).first())
            self.aseguradoras.append(seguro)
            condicion = self.catalogo(models.CondicionCronica, f'{etiqueta} condición {indice + 1}', perfiles.CONDICIONES[indice])
            self.condiciones.append(condicion)
            examen = self.catalogo(models.CatalogoExamen, f'{etiqueta} examen {indice + 1}', perfiles.EXAMENES[indice],
                                   defaults={'precio': Decimal('75.00') + indice * 25})
            self.examenes.append(examen)
            procedimiento = self.catalogo(models.Procedimiento, f'{etiqueta} procedimiento {indice + 1}',
                                          perfiles.PROCEDIMIENTOS[indice], defaults={'precio': Decimal('50.00') + indice * 25})
            self.procedimientos.append(procedimiento)

        self.especialidades = []
        self.medicos = []
        self.turnos = {}
        for indice, nombre in enumerate(('General', 'Interna', 'Cardiología', 'Dermatología')):
            medico_previo = models.Medico.objects.filter(num_colegiado=f'D{self.huella}M{indice + 1:02}').first()
            especialidad = self.catalogo(models.Especialidad, f'{etiqueta} {nombre}', perfiles.ESPECIALIDADES[indice],
                existente=medico_previo.id_especialidad if medico_previo is not None else None)
            self.especialidades.append(especialidad)
            medico, _ = self.registro(models.Medico, num_colegiado=f'D{self.huella}M{indice + 1:02}', defaults={
                **perfiles.MEDICOS[indice],
                'id_especialidad': especialidad, 'honorario_consulta': Decimal('150.00') + indice * 25,
                'activo': True,
            })
            self.medicos.append(medico)
            for dia in range(1, 8):
                turno, _ = self.registro(models.Turno, id_medico=medico,
                    id_consultorio=self.consultorios[indice % 3], dia_semana=dia,
                    hora_inicio=time(8), hora_fin=time(17),
                    defaults={'duracion_consulta_min': 30, 'activo': True})
                self.turnos[(indice, dia)] = turno
        for indice, medico in enumerate(self.medicos):
            self.relacion('medico_subespecialidad', id_medico=medico.pk,
                          id_especialidad=self.especialidades[(indice + 1) % 4].pk)

        self.componentes = []
        self.medicamentos = []
        for indice in range(6):
            componente = self.catalogo(models.ComponenteActivo, f'{etiqueta} componente {indice + 1}', perfiles.COMPONENTES[indice])
            self.componentes.append(componente)
            medicamento = self.catalogo(models.Medicamento, f'{etiqueta} medicamento {indice + 1}', perfiles.MEDICAMENTOS[indice],
                campo='nombre_comercial', defaults={'precio_unitario': Decimal('5.00') + indice, 'stock_farmacia': 150, 'activo': True})
            self.medicamentos.append(medicamento)
            self.relacion('medicamento_componente', id_medicamento=medicamento.pk, id_componente=componente.pk)
        self.diagnosticos = []
        for indice in range(3):
            diagnostico, _ = self.registro(models.DiagnosticoCIE10, codigo_cie10=f'T{self.huella[:6]}{indice + 1:02}',
                defaults=perfiles.DIAGNOSTICOS[indice])
            self.diagnosticos.append(diagnostico)

    def paciente(self, numero):
        etiqueta = f'{self.lote}-{numero:03}'
        base_dpi = int(self.huella, 16) % 10000000
        paciente, _ = self.registro(models.Paciente, num_expediente=etiqueta, defaults={
            **perfiles.perfil_paciente(numero),
            'dpi': f'000{base_dpi:07}{numero:03}', 'fecha_nacimiento': date(1980 + numero % 25, 1 + numero % 12, 10),
            'sexo': 'F' if numero % 2 else 'M', 'tipo_sangre': ('O+', 'A+', 'B+')[numero % 3],
            'fecha_registro': datetime.combine(self.fecha_base - timedelta(days=200), time(8)),
        })
        poliza, _ = self.registro(models.Poliza, numero_poliza=f'{etiqueta}-POL', id_paciente=paciente, defaults={
            'id_aseguradora': self.aseguradoras[(numero - 1) % 3],
            'porcentaje_cobertura': Decimal((60, 70, 80)[numero % 3]), 'deducible': Decimal('25.00'),
            'fecha_inicio': self.fecha_base - timedelta(days=365),
            'fecha_fin': self.fecha_base + timedelta(days=365), 'estado': 'Activa',
        })
        self.relacion('paciente_condicion', id_paciente=paciente.pk,
            id_condicion=self.condiciones[(numero - 1) % 3].pk,
            fecha_diagnostico=self.fecha_base - timedelta(days=180),
            observaciones=perfiles.perfil_visita(numero, 0, (numero - 1) % 4)['observaciones_condicion'])
        self.registro(models.AlergiaPaciente, id_paciente=paciente, id_componente=self.componentes[(numero + 2) % 6],
            defaults={'reaccion': perfiles.perfil_visita(numero, 0, (numero - 1) % 4)['reaccion_alergia'], 'severidad': 'Leve'})
        for visita in range(2):
            self.visita(paciente, poliza, numero, visita)

    def visita(self, paciente, poliza, numero, visita):
        indice = (numero - 1 + visita) % 4
        fecha = self.fecha_base - timedelta(days=(numero - 1) * 2 + (1 - visita))
        hora = datetime.combine(fecha, time(9 + numero % 6))
        medico = self.medicos[indice]
        perfil = perfiles.perfil_visita(numero, visita, indice)
        codigo_factura, factura_previa = self.factura_existente(numero, visita, paciente)
        cita_previa = factura_previa.id_consulta.id_cita if factura_previa is not None else (
            models.Cita.objects.filter(id_paciente=paciente,
                motivo_consulta=f'{self.lote}: cita de prueba {numero:03}-{visita + 1}').first())
        cita, _ = self.registro(models.Cita, id_paciente=paciente,
            motivo_consulta=perfil['motivo_consulta'], existente=cita_previa, defaults={
                'id_medico': medico, 'id_consultorio': self.consultorios[indice % 3],
                'id_turno': self.turnos[(indice, fecha.isoweekday())], 'fecha_hora_programada': hora,
                'canal_reserva': 'Presencial' if visita == 0 else 'Telefonica', 'estado': 'Atendida',
                'fecha_creacion': hora - timedelta(days=1),
            })
        self.registro(models.Triaje, id_cita=cita, defaults={
            'id_enfermero': self.enfermeros[indice % 3], 'fecha_hora_triaje': hora + timedelta(minutes=5),
            'peso_kg': Decimal('60.00') + numero, 'talla_cm': Decimal('160.00') + numero % 20,
            'presion_sistolica': 110 + numero % 20, 'presion_diastolica': 70 + numero % 15,
            'frecuencia_cardiaca': 65 + numero % 20, 'temperatura_c': Decimal('36.5'),
            'nivel_urgencia': 1 + (numero + visita) % 5, 'observaciones': perfil['observaciones_triaje'],
        })
        consulta, _ = self.registro(models.Consulta, id_cita=cita, defaults={
            'fecha_hora_consulta': hora + timedelta(minutes=15),
            'anamnesis': perfil['anamnesis'],
            'examen_fisico': perfil['examen_fisico'],
            'plan_tratamiento': perfil['plan_tratamiento'],
        })
        self.relacion('consulta_diagnostico', id_consulta=consulta.pk,
            codigo_cie10=self.diagnosticos[(numero + visita) % 3].pk, tipo='Principal')
        procedimiento = self.procedimientos[(numero + visita) % 3]
        self.relacion('consulta_procedimiento', id_consulta=consulta.pk, id_procedimiento=procedimiento.pk, cantidad=1)
        receta, _ = self.registro(models.Receta, id_consulta=consulta, defaults={
            'fecha_emision': hora + timedelta(minutes=25), 'estado': 'Emitida',
        })
        medicamento = self.medicamentos[(numero - 1 + visita) % 6]
        self.registro(models.DetalleReceta, id_receta=receta, id_medicamento=medicamento, defaults={
            'dosis': perfil['dosis'], 'via_administracion': perfil['via_administracion'],
            'frecuencia_horas': 8, 'duracion_dias': 3, 'cantidad_despachar': 6,
        })
        examen = self.examenes[(numero + visita) % 3]
        self.registro(models.OrdenExamen, id_consulta=consulta, id_examen=examen, defaults={
            'fecha_solicitud': hora + timedelta(minutes=20), 'estado': 'Completado',
            'resultado': perfil['resultado_examen'],
        })
        aplica_seguro = not (numero % 4 == 0 and visita == 1)
        factura, creada = self.registro(models.Factura, numero_factura=codigo_factura, id_consulta=consulta, defaults={
            'id_poliza': poliza if aplica_seguro else None, 'fecha_emision': hora + timedelta(hours=1),
            'tipo': 'Total', 'estado_pago_paciente': 'Parcial',
            'estado_cobro_aseguradora': 'Pendiente' if aplica_seguro else 'NoAplica',
        })
        if not creada:
            # Los importes de una factura existente pueden haber sido editados por el usuario.
            # No insertar líneas ni guardar de nuevo: evitar recalcular registros anteriores.
            self.existentes['DETALLE_FACTURA'] += models.DetalleFactura.objects.filter(id_factura=factura).count()
            self.existentes['PAGO'] += models.Pago.objects.filter(id_factura=factura).count()
            return
        conceptos = [
            ('Honorarios', 1, medico.honorario_consulta, {}),
            ('Medicamento', 6, medicamento.precio_unitario, {'id_medicamento': medicamento}),
            ('Examen', 1, examen.precio, {'id_examen': examen}),
            ('Procedimiento', 1, procedimiento.precio, {'id_procedimiento': procedimiento}),
        ]
        for concepto, cantidad, precio, referencia in conceptos:
            self.registro(models.DetalleFactura, id_factura=factura, tipo_concepto=concepto,
                descripcion=self.descripcion_concepto(concepto, medico=medico, medicamento=medicamento,
                    examen=examen, procedimiento=procedimiento), defaults={
                    'cantidad': cantidad, 'precio_unitario': precio, **referencia,
                })
        factura.refresh_from_db()
        if aplica_seguro:
            factura.deducible_aplicado = Decimal('25.00')
            factura.save(update_fields={'deducible_aplicado'})
        self.registro(models.Pago, id_factura=factura, referencia=f'{codigo_factura}-PAGO', defaults={
            'fecha_pago': hora + timedelta(hours=2),
            'monto': (factura.monto_paciente / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'pagador': 'Paciente', 'metodo': 'Efectivo',
        })

    @staticmethod
    def descripcion_concepto(concepto, *, medico=None, medicamento=None, examen=None, procedimiento=None):
        return {
            'Honorarios': f'Consulta externa con {medico.nombres} {medico.apellidos}' if medico else 'Consulta externa',
            'Medicamento': f'Dispensación de {medicamento.nombre_comercial}' if medicamento else 'Dispensación de medicamentos',
            'Examen': examen.nombre if examen else 'Estudio de laboratorio',
            'Procedimiento': procedimiento.nombre if procedimiento else 'Procedimiento en consulta externa',
        }[concepto]

    def actualizar_textos(self, objeto, anteriores, nuevos):
        """Cambiar exclusivamente textos reconocidos, sin ejecutar save ni recalcular."""
        if objeto is None:
            return
        clave = (objeto._meta.db_table, objeto.pk)
        if clave not in self._inspeccionados:
            self.existentes[clave[0]] += 1
            self._inspeccionados.add(clave)
        cambios = {}
        for nombre, anterior in anteriores.items():
            if nombre not in nuevos or nuevos[nombre] == anterior or getattr(objeto, nombre) != anterior:
                continue
            campo = objeto._meta.get_field(nombre)
            if campo.is_relation or campo.primary_key or campo.get_internal_type() not in ('CharField', 'TextField'):
                raise ValidationError(f'La actualización del lote solo admite textos: {nombre}.')
            cambios[nombre] = campo.clean(nuevos[nombre], objeto)
        if cambios:
            type(objeto).objects.filter(pk=objeto.pk).update(**cambios)
            for nombre, valor in cambios.items():
                setattr(objeto, nombre, valor)
            if clave not in self._actualizados:
                self.actualizados[clave[0]] += 1
                self._actualizados.add(clave)

    def naturalizar_catalogo(self, modelo, anterior, perfil, *, campo='nombre', anteriores=None, existente=None):
        # Una coincidencia con un nombre natural no prueba propiedad del lote.
        objeto = existente if existente is not None else modelo.objects.filter(**{campo: anterior}).first()
        if objeto is None:
            return
        nuevos = dict(perfil)
        if getattr(objeto, campo) == anterior and modelo._meta.get_field(campo).unique:
            nombre = perfil[campo]
            if modelo.objects.filter(**{campo: nombre}).exclude(pk=objeto.pk).exists():
                nombre = f'{nombre} ({self.lote})'
                if modelo.objects.filter(**{campo: nombre}).exclude(pk=objeto.pk).exists():
                    raise ValidationError(f'El nombre alternativo del catálogo {modelo._meta.db_table} ya está ocupado.')
            nuevos[campo] = nombre
        self.actualizar_textos(objeto, {campo: anterior, **(anteriores or {})}, nuevos)

    def nombres_catalogo(self, anterior, natural):
        return (anterior, natural, f'{natural} ({self.lote})')

    def naturalizar_lote(self):
        """Actualizar el lote legado sin insertar, borrar ni mover registros."""
        pacientes = []
        for numero in range(1, self.pacientes + 1):
            paciente = models.Paciente.objects.filter(num_expediente=f'{self.lote}-{numero:03}').first()
            if paciente is None:
                raise ValidationError(f'No existe el paciente {self.lote}-{numero:03}; no se modificó el lote.')
            for visita in range(2):
                _, factura = self.factura_existente(numero, visita, paciente)
                if factura is None:
                    raise ValidationError(f'Falta una factura de {self.lote}-{numero:03}; no se modificó el lote.')
            pacientes.append(paciente)

        etiqueta = f'{self.lote} PRUEBA'
        for indice in range(3):
            self.naturalizar_catalogo(models.Sede, f'{etiqueta} sede {indice + 1}', perfiles.SEDES[indice], anteriores={
                'tipo': 'Clinica', 'direccion': 'Dirección ficticia para demostración',
                'municipio': 'Municipio de prueba', 'departamento': 'Departamento de prueba', 'telefono': '00000000',
            })
            self.naturalizar_catalogo(models.Aseguradora, f'{etiqueta} seguro {indice + 1}', perfiles.ASEGURADORAS[indice],
                existente=models.Aseguradora.objects.filter(nit=f'D{self.huella}A{indice + 1:02}').first(), anteriores={
                    'telefono': '00000000', 'correo': f'seguro{indice + 1}@example.com', 'direccion': 'Dirección ficticia',
                })
            self.naturalizar_catalogo(models.CondicionCronica, f'{etiqueta} condición {indice + 1}', perfiles.CONDICIONES[indice],
                anteriores={'descripcion': 'Condición ficticia para probar relaciones del expediente.'})
            self.naturalizar_catalogo(models.CatalogoExamen, f'{etiqueta} examen {indice + 1}', perfiles.EXAMENES[indice])
            self.naturalizar_catalogo(models.Procedimiento, f'{etiqueta} procedimiento {indice + 1}', perfiles.PROCEDIMIENTOS[indice])
            enfermero = models.Enfermero.objects.filter(num_colegiado=f'D{self.huella}E{indice + 1:02}').first()
            self.actualizar_textos(enfermero, {'nombres': f'Enfermero de prueba {indice + 1}',
                'apellidos': self.lote, 'telefono': '00000000'}, perfiles.ENFERMEROS[indice])
            diagnostico = models.DiagnosticoCIE10.objects.filter(codigo_cie10=f'T{self.huella[:6]}{indice + 1:02}').first()
            self.actualizar_textos(diagnostico,
                {'descripcion': f'{etiqueta}: diagnóstico simulado {indice + 1}; código ficticio.'}, perfiles.DIAGNOSTICOS[indice])
        for indice, nombre in enumerate(('General', 'Interna', 'Cardiología', 'Dermatología')):
            self.naturalizar_catalogo(models.Especialidad, f'{etiqueta} {nombre}', perfiles.ESPECIALIDADES[indice],
                anteriores={'descripcion': 'Especialidad de demostración.'})
            medico = models.Medico.objects.filter(num_colegiado=f'D{self.huella}M{indice + 1:02}').first()
            self.actualizar_textos(medico, {'nombres': f'Médico de prueba {indice + 1}', 'apellidos': self.lote,
                'telefono': '00000000', 'correo': f'medico{indice + 1}@example.com'}, perfiles.MEDICOS[indice])
        for indice in range(6):
            self.naturalizar_catalogo(models.ComponenteActivo, f'{etiqueta} componente {indice + 1}', perfiles.COMPONENTES[indice])
            self.naturalizar_catalogo(models.Medicamento, f'{etiqueta} medicamento {indice + 1}', perfiles.MEDICAMENTOS[indice],
                campo='nombre_comercial', anteriores={'forma_farmaceutica': 'Simulada', 'concentracion': 'Producto de prueba'})

        for numero, paciente in enumerate(pacientes, 1):
            self.actualizar_textos(paciente, {
                'nombres': f'Paciente de prueba {numero:03}', 'apellidos': self.lote,
                'direccion': 'Dirección ficticia; registro de demostración', 'telefono': '00000000',
                'correo': f'paciente{numero:03}@example.com', 'contacto_emergencia_nombre': 'Contacto ficticio de prueba',
                'contacto_emergencia_telefono': '00000000', 'contacto_emergencia_parentesco': 'Familiar de prueba',
            }, perfiles.perfil_paciente(numero))
            perfil = perfiles.perfil_visita(numero, 0, (numero - 1) % 4)
            indice_condicion = (numero - 1) % 3
            condiciones = models.CondicionCronica.objects.filter(nombre__in=self.nombres_catalogo(
                f'{etiqueta} condición {indice_condicion + 1}', perfiles.CONDICIONES[indice_condicion]['nombre']))
            with connection.cursor() as cursor:
                for condicion in condiciones:
                    cursor.execute('UPDATE [PACIENTE_CONDICION] SET [observaciones] = %s '
                        'WHERE [id_paciente] = %s AND [id_condicion] = %s AND [observaciones] = %s',
                        [perfil['observaciones_condicion'], paciente.pk, condicion.pk, 'Relación ficticia de prueba.'])
                    if cursor.rowcount:
                        self.actualizados['PACIENTE_CONDICION'] += cursor.rowcount
            indice_componente = (numero + 2) % 6
            componentes = models.ComponenteActivo.objects.filter(nombre__in=self.nombres_catalogo(
                f'{etiqueta} componente {indice_componente + 1}', perfiles.COMPONENTES[indice_componente]['nombre']))
            for alergia in models.AlergiaPaciente.objects.filter(id_paciente=paciente, id_componente__in=componentes):
                self.actualizar_textos(alergia, {'reaccion': 'Reacción simulada para probar el expediente.'},
                    {'reaccion': perfil['reaccion_alergia']})
            for visita in range(2):
                self.naturalizar_visita(paciente, numero, visita)

    def naturalizar_visita(self, paciente, numero, visita):
        indice = (numero - 1 + visita) % 4
        perfil = perfiles.perfil_visita(numero, visita, indice)
        _, factura = self.factura_existente(numero, visita, paciente)
        consulta = factura.id_consulta
        cita = consulta.id_cita
        self.actualizar_textos(cita, {'motivo_consulta': f'{self.lote}: cita de prueba {numero:03}-{visita + 1}'}, perfil)
        self.actualizar_textos(models.Triaje.objects.filter(id_cita=cita).first(),
            {'observaciones': 'Triaje ficticio para demostración.'}, {'observaciones': perfil['observaciones_triaje']})
        self.actualizar_textos(consulta, {
            'anamnesis': f'{self.lote}: historia de prueba del paciente {numero:03}, visita {visita + 1}.',
            'examen_fisico': 'Examen simulado; datos exclusivamente de demostración.',
            'plan_tratamiento': 'Plan ficticio de prueba; no constituye una indicación médica.',
        }, perfil)
        receta = models.Receta.objects.filter(id_consulta=consulta).first()
        if receta is not None:
            for detalle in models.DetalleReceta.objects.filter(id_receta=receta):
                self.actualizar_textos(detalle, {'dosis': 'Simulación: no administrar', 'via_administracion': 'Simulada'}, perfil)
        for orden in models.OrdenExamen.objects.filter(id_consulta=consulta):
            self.actualizar_textos(orden, {'resultado': 'Resultado ficticio de demostración.'},
                {'resultado': perfil['resultado_examen']})
        for detalle in models.DetalleFactura.objects.select_related('id_medicamento', 'id_examen', 'id_procedimiento').filter(id_factura=factura):
            if detalle.tipo_concepto in ('Honorarios', 'Medicamento', 'Examen', 'Procedimiento'):
                self.actualizar_textos(detalle, {'descripcion': f'{self.lote}: {detalle.tipo_concepto} de prueba'}, {
                    'descripcion': self.descripcion_concepto(detalle.tipo_concepto, medico=cita.id_medico,
                        medicamento=detalle.id_medicamento, examen=detalle.id_examen, procedimiento=detalle.id_procedimiento),
                })


def cargar_datos_prueba(*, lote=LOTE_PREDETERMINADO, pacientes=20, fecha_base=FECHA_BASE, dry_run=False, naturalizar=False):
    """Agregar un lote ficticio completo o revertirlo todo si ocurre cualquier error."""
    fecha_base = validar_opciones(lote=lote, pacientes=pacientes, fecha_base=fecha_base)
    carga = CargaPrueba(lote, pacientes, fecha_base)
    with transaction.atomic():
        if naturalizar:
            carga.naturalizar_lote()
        else:
            carga.catalogos()
            for numero in range(1, pacientes + 1):
                carga.paciente(numero)
        if dry_run:
            transaction.set_rollback(True)
    return {'creados': dict(sorted(carga.creados.items())),
            'existentes': dict(sorted(carga.existentes.items())),
            'actualizados': dict(sorted(carga.actualizados.items())), 'simulacion': bool(dry_run)}
