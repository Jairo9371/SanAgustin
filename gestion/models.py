"""Mapeo a las tablas SQL Server existentes. NO crear estas tablas mediante Django."""
from datetime import datetime
from copy import copy
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, router, transaction
from django.db.models import Sum
from .facturacion import calcular_importes, subtotal_de_linea

class Paciente(models.Model):
    id_paciente = models.AutoField(primary_key=True, db_column='id_paciente', verbose_name='Id paciente')
    num_expediente = models.CharField(max_length=20, unique=True, db_column='num_expediente', verbose_name='Num expediente')
    dpi = models.CharField(max_length=13, unique=True, db_column='dpi', verbose_name='Dpi')
    nombres = models.CharField(max_length=80, db_column='nombres', verbose_name='Nombres')
    apellidos = models.CharField(max_length=80, db_column='apellidos', verbose_name='Apellidos')
    fecha_nacimiento = models.DateField(db_column='fecha_nacimiento', verbose_name='Fecha nacimiento')
    sexo = models.CharField(max_length=1, db_column='sexo', verbose_name='Sexo')
    tipo_sangre = models.CharField(max_length=3, null=True, blank=True, db_column='tipo_sangre', verbose_name='Tipo sangre')
    direccion = models.CharField(max_length=200, null=True, blank=True, db_column='direccion', verbose_name='Direccion')
    telefono = models.CharField(max_length=15, null=True, blank=True, db_column='telefono', verbose_name='Telefono')
    correo = models.CharField(max_length=100, null=True, blank=True, db_column='correo', verbose_name='Correo')
    contacto_emergencia_nombre = models.CharField(max_length=100, db_column='contacto_emergencia_nombre', verbose_name='Contacto emergencia nombre')
    contacto_emergencia_telefono = models.CharField(max_length=15, db_column='contacto_emergencia_telefono', verbose_name='Contacto emergencia telefono')
    contacto_emergencia_parentesco = models.CharField(max_length=30, null=True, blank=True, db_column='contacto_emergencia_parentesco', verbose_name='Contacto emergencia parentesco')
    fecha_registro = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_registro', verbose_name='Fecha registro')

    class Meta:
        managed = False
        db_table = 'PACIENTE'
        verbose_name = 'Pacientes'
        verbose_name_plural = 'Pacientes'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class CondicionCronica(models.Model):
    id_condicion = models.AutoField(primary_key=True, db_column='id_condicion', verbose_name='Id condicion')
    nombre = models.CharField(max_length=100, unique=True, db_column='nombre', verbose_name='Nombre')
    descripcion = models.CharField(max_length=250, null=True, blank=True, db_column='descripcion', verbose_name='Descripcion')

    class Meta:
        managed = False
        db_table = 'CONDICION_CRONICA'
        verbose_name = 'Condiciones crónicas'
        verbose_name_plural = 'Condiciones crónicas'

    def __str__(self):
        return str(self.nombre)

class Aseguradora(models.Model):
    id_aseguradora = models.AutoField(primary_key=True, db_column='id_aseguradora', verbose_name='Id aseguradora')
    nombre = models.CharField(max_length=100, unique=True, db_column='nombre', verbose_name='Nombre')
    nit = models.CharField(max_length=15, unique=True, null=True, blank=True, db_column='nit', verbose_name='Nit')
    telefono = models.CharField(max_length=15, null=True, blank=True, db_column='telefono', verbose_name='Telefono')
    correo = models.CharField(max_length=100, null=True, blank=True, db_column='correo', verbose_name='Correo')
    direccion = models.CharField(max_length=200, null=True, blank=True, db_column='direccion', verbose_name='Direccion')

    class Meta:
        managed = False
        db_table = 'ASEGURADORA'
        verbose_name = 'Aseguradoras'
        verbose_name_plural = 'Aseguradoras'

    def __str__(self):
        return str(self.nombre)

class Poliza(models.Model):
    id_poliza = models.AutoField(primary_key=True, db_column='id_poliza', verbose_name='Id poliza')
    id_paciente = models.ForeignKey('Paciente', on_delete=models.PROTECT, db_column='id_paciente', verbose_name='Id paciente')
    id_aseguradora = models.ForeignKey('Aseguradora', on_delete=models.PROTECT, db_column='id_aseguradora', verbose_name='Id aseguradora')
    numero_poliza = models.CharField(max_length=30, db_column='numero_poliza', verbose_name='Numero poliza')
    porcentaje_cobertura = models.DecimalField(max_digits=5, decimal_places=2, db_column='porcentaje_cobertura', verbose_name='Porcentaje cobertura')
    deducible = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_column='deducible', verbose_name='Deducible')
    fecha_inicio = models.DateField(db_column='fecha_inicio', verbose_name='Fecha inicio')
    fecha_fin = models.DateField(null=True, blank=True, db_column='fecha_fin', verbose_name='Fecha fin')
    estado = models.CharField(max_length=10, default='Activa', db_column='estado', verbose_name='Estado')

    class Meta:
        managed = False
        db_table = 'POLIZA'
        verbose_name = 'Pólizas'
        verbose_name_plural = 'Pólizas'

    def __str__(self):
        return str(self.numero_poliza)

class Sede(models.Model):
    id_sede = models.AutoField(primary_key=True, db_column='id_sede', verbose_name='Id sede')
    nombre = models.CharField(max_length=100, unique=True, db_column='nombre', verbose_name='Nombre')
    tipo = models.CharField(max_length=15, db_column='tipo', verbose_name='Tipo')
    direccion = models.CharField(max_length=200, null=True, blank=True, db_column='direccion', verbose_name='Direccion')
    municipio = models.CharField(max_length=60, null=True, blank=True, db_column='municipio', verbose_name='Municipio')
    departamento = models.CharField(max_length=60, null=True, blank=True, db_column='departamento', verbose_name='Departamento')
    telefono = models.CharField(max_length=15, null=True, blank=True, db_column='telefono', verbose_name='Telefono')

    class Meta:
        managed = False
        db_table = 'SEDE'
        verbose_name = 'Sedes'
        verbose_name_plural = 'Sedes'

    def __str__(self):
        return str(self.nombre)

class Consultorio(models.Model):
    id_consultorio = models.AutoField(primary_key=True, db_column='id_consultorio', verbose_name='Id consultorio')
    id_sede = models.ForeignKey('Sede', on_delete=models.PROTECT, db_column='id_sede', verbose_name='Id sede')
    numero = models.CharField(max_length=10, db_column='numero', verbose_name='Numero')
    piso = models.CharField(max_length=10, null=True, blank=True, db_column='piso', verbose_name='Piso')

    class Meta:
        managed = False
        db_table = 'CONSULTORIO'
        verbose_name = 'Consultorios'
        verbose_name_plural = 'Consultorios'

    def __str__(self):
        return f"Consultorios #{self.pk}"

class Especialidad(models.Model):
    id_especialidad = models.AutoField(primary_key=True, db_column='id_especialidad', verbose_name='Id especialidad')
    nombre = models.CharField(max_length=80, unique=True, db_column='nombre', verbose_name='Nombre')
    descripcion = models.CharField(max_length=250, null=True, blank=True, db_column='descripcion', verbose_name='Descripcion')

    class Meta:
        managed = False
        db_table = 'ESPECIALIDAD'
        verbose_name = 'Especialidades'
        verbose_name_plural = 'Especialidades'

    def __str__(self):
        return str(self.nombre)

class Medico(models.Model):
    id_medico = models.AutoField(primary_key=True, db_column='id_medico', verbose_name='Id medico')
    num_colegiado = models.CharField(max_length=15, unique=True, db_column='num_colegiado', verbose_name='Num colegiado')
    nombres = models.CharField(max_length=80, db_column='nombres', verbose_name='Nombres')
    apellidos = models.CharField(max_length=80, db_column='apellidos', verbose_name='Apellidos')
    telefono = models.CharField(max_length=15, null=True, blank=True, db_column='telefono', verbose_name='Telefono')
    correo = models.CharField(max_length=100, null=True, blank=True, db_column='correo', verbose_name='Correo')
    id_especialidad = models.ForeignKey('Especialidad', on_delete=models.PROTECT, db_column='id_especialidad', verbose_name='Id especialidad')
    honorario_consulta = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_column='honorario_consulta', verbose_name='Honorario consulta')
    activo = models.BooleanField(default=True, db_column='activo', verbose_name='Activo')

    class Meta:
        managed = False
        db_table = 'MEDICO'
        verbose_name = 'Médicos'
        verbose_name_plural = 'Médicos'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class Turno(models.Model):
    id_turno = models.AutoField(primary_key=True, db_column='id_turno', verbose_name='Id turno')
    id_medico = models.ForeignKey('Medico', on_delete=models.PROTECT, db_column='id_medico', verbose_name='Id medico')
    id_consultorio = models.ForeignKey('Consultorio', on_delete=models.PROTECT, db_column='id_consultorio', verbose_name='Id consultorio')
    dia_semana = models.PositiveSmallIntegerField(db_column='dia_semana', verbose_name='Día de la semana',
        validators=[MinValueValidator(1), MaxValueValidator(7)], help_text='1 = lunes, 7 = domingo.')
    hora_inicio = models.TimeField(db_column='hora_inicio', verbose_name='Hora inicio')
    hora_fin = models.TimeField(db_column='hora_fin', verbose_name='Hora fin')
    duracion_consulta_min = models.SmallIntegerField(db_column='duracion_consulta_min', verbose_name='Duracion consulta min')
    activo = models.BooleanField(default=True, db_column='activo', verbose_name='Activo')

    class Meta:
        managed = False
        db_table = 'TURNO'
        verbose_name = 'Turnos médicos'
        verbose_name_plural = 'Turnos médicos'

    def __str__(self):
        return f"Turnos médicos #{self.pk}"

class Enfermero(models.Model):
    id_enfermero = models.AutoField(primary_key=True, db_column='id_enfermero', verbose_name='Id enfermero')
    num_colegiado = models.CharField(max_length=15, unique=True, db_column='num_colegiado', verbose_name='Num colegiado')
    nombres = models.CharField(max_length=80, db_column='nombres', verbose_name='Nombres')
    apellidos = models.CharField(max_length=80, db_column='apellidos', verbose_name='Apellidos')
    telefono = models.CharField(max_length=15, null=True, blank=True, db_column='telefono', verbose_name='Telefono')
    id_sede = models.ForeignKey('Sede', on_delete=models.PROTECT, db_column='id_sede', verbose_name='Id sede')

    class Meta:
        managed = False
        db_table = 'ENFERMERO'
        verbose_name = 'Enfermeros'
        verbose_name_plural = 'Enfermeros'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class Cita(models.Model):
    id_cita = models.AutoField(primary_key=True, db_column='id_cita', verbose_name='Id cita')
    id_paciente = models.ForeignKey('Paciente', on_delete=models.PROTECT, db_column='id_paciente', verbose_name='Id paciente')
    id_medico = models.ForeignKey('Medico', on_delete=models.PROTECT, db_column='id_medico', verbose_name='Id medico')
    id_consultorio = models.ForeignKey('Consultorio', on_delete=models.PROTECT, db_column='id_consultorio', verbose_name='Id consultorio')
    id_turno = models.ForeignKey('Turno', on_delete=models.PROTECT, null=True, blank=True, db_column='id_turno', verbose_name='Id turno')
    fecha_hora_programada = models.DateTimeField(db_column='fecha_hora_programada', verbose_name='Fecha hora programada')
    canal_reserva = models.CharField(max_length=12, db_column='canal_reserva', verbose_name='Canal reserva')
    motivo_consulta = models.CharField(max_length=250, db_column='motivo_consulta', verbose_name='Motivo consulta')
    estado = models.CharField(max_length=15, default='Programada', db_column='estado', verbose_name='Estado')
    fecha_creacion = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_creacion', verbose_name='Fecha creacion')

    class Meta:
        managed = False
        db_table = 'CITA'
        verbose_name = 'Citas'
        verbose_name_plural = 'Citas'

    def __str__(self):
        return f"Citas #{self.pk}"

class Triaje(models.Model):
    id_triaje = models.AutoField(primary_key=True, db_column='id_triaje', verbose_name='Id triaje')
    id_cita = models.OneToOneField('Cita', on_delete=models.PROTECT, db_column='id_cita', verbose_name='Id cita')
    id_enfermero = models.ForeignKey('Enfermero', on_delete=models.PROTECT, db_column='id_enfermero', verbose_name='Id enfermero')
    fecha_hora_triaje = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_hora_triaje', verbose_name='Fecha hora triaje')
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, db_column='peso_kg', verbose_name='Peso kg')
    talla_cm = models.DecimalField(max_digits=5, decimal_places=2, db_column='talla_cm', verbose_name='Talla cm')
    presion_sistolica = models.SmallIntegerField(db_column='presion_sistolica', verbose_name='Presion sistolica')
    presion_diastolica = models.SmallIntegerField(db_column='presion_diastolica', verbose_name='Presion diastolica')
    frecuencia_cardiaca = models.SmallIntegerField(db_column='frecuencia_cardiaca', verbose_name='Frecuencia cardiaca')
    temperatura_c = models.DecimalField(max_digits=4, decimal_places=1, db_column='temperatura_c', verbose_name='Temperatura c')
    nivel_urgencia = models.PositiveSmallIntegerField(db_column='nivel_urgencia', verbose_name='Nivel urgencia',
        validators=[MinValueValidator(0), MaxValueValidator(255)])
    observaciones = models.CharField(max_length=250, null=True, blank=True, db_column='observaciones', verbose_name='Observaciones')

    class Meta:
        managed = False
        db_table = 'TRIAJE'
        verbose_name = 'Triajes'
        verbose_name_plural = 'Triajes'

    def __str__(self):
        return f"Triajes #{self.pk}"

class DiagnosticoCIE10(models.Model):
    codigo_cie10 = models.CharField(max_length=10, primary_key=True, db_column='codigo_cie10', verbose_name='Codigo cie10')
    descripcion = models.CharField(max_length=250, db_column='descripcion', verbose_name='Descripcion')

    class Meta:
        managed = False
        db_table = 'DIAGNOSTICO_CIE10'
        verbose_name = 'Diagnósticos CIE-10'
        verbose_name_plural = 'Diagnósticos CIE-10'

    def __str__(self):
        return str(self.codigo_cie10)

class Consulta(models.Model):
    id_consulta = models.AutoField(primary_key=True, db_column='id_consulta', verbose_name='Id consulta')
    id_cita = models.OneToOneField('Cita', on_delete=models.PROTECT, db_column='id_cita', verbose_name='Id cita')
    fecha_hora_consulta = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_hora_consulta', verbose_name='Fecha hora consulta')
    anamnesis = models.TextField(db_column='anamnesis', verbose_name='Anamnesis')
    examen_fisico = models.TextField(null=True, blank=True, db_column='examen_fisico', verbose_name='Examen fisico')
    plan_tratamiento = models.CharField(max_length=500, null=True, blank=True, db_column='plan_tratamiento', verbose_name='Plan tratamiento')

    class Meta:
        managed = False
        db_table = 'CONSULTA'
        verbose_name = 'Consultas médicas'
        verbose_name_plural = 'Consultas médicas'

    def __str__(self):
        return f"Consultas médicas #{self.pk}"

class ComponenteActivo(models.Model):
    id_componente = models.AutoField(primary_key=True, db_column='id_componente', verbose_name='Id componente')
    nombre = models.CharField(max_length=100, unique=True, db_column='nombre', verbose_name='Nombre')

    class Meta:
        managed = False
        db_table = 'COMPONENTE_ACTIVO'
        verbose_name = 'Componentes activos'
        verbose_name_plural = 'Componentes activos'

    def __str__(self):
        return str(self.nombre)

class Medicamento(models.Model):
    id_medicamento = models.AutoField(primary_key=True, db_column='id_medicamento', verbose_name='Id medicamento')
    nombre_comercial = models.CharField(max_length=100, db_column='nombre_comercial', verbose_name='Nombre comercial')
    forma_farmaceutica = models.CharField(max_length=30, null=True, blank=True, db_column='forma_farmaceutica', verbose_name='Forma farmaceutica')
    concentracion = models.CharField(max_length=30, null=True, blank=True, db_column='concentracion', verbose_name='Concentracion')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, db_column='precio_unitario', verbose_name='Precio unitario')
    stock_farmacia = models.IntegerField(default=0, db_column='stock_farmacia', verbose_name='Stock farmacia')
    activo = models.BooleanField(default=True, db_column='activo', verbose_name='Activo')

    class Meta:
        managed = False
        db_table = 'MEDICAMENTO'
        verbose_name = 'Medicamentos'
        verbose_name_plural = 'Medicamentos'

    def __str__(self):
        return str(self.nombre_comercial)

class Receta(models.Model):
    id_receta = models.AutoField(primary_key=True, db_column='id_receta', verbose_name='Id receta')
    id_consulta = models.OneToOneField('Consulta', on_delete=models.PROTECT, db_column='id_consulta', verbose_name='Id consulta')
    fecha_emision = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_emision', verbose_name='Fecha emision')
    estado = models.CharField(max_length=12, default='Emitida', db_column='estado', verbose_name='Estado')

    class Meta:
        managed = False
        db_table = 'RECETA'
        verbose_name = 'Recetas'
        verbose_name_plural = 'Recetas'

    def __str__(self):
        return f"Recetas #{self.pk}"

class DetalleReceta(models.Model):
    id_detalle_receta = models.AutoField(primary_key=True, db_column='id_detalle_receta', verbose_name='Id detalle receta')
    id_receta = models.ForeignKey('Receta', on_delete=models.PROTECT, db_column='id_receta', verbose_name='Id receta')
    id_medicamento = models.ForeignKey('Medicamento', on_delete=models.PROTECT, db_column='id_medicamento', verbose_name='Id medicamento')
    dosis = models.CharField(max_length=50, db_column='dosis', verbose_name='Dosis')
    via_administracion = models.CharField(max_length=20, db_column='via_administracion', verbose_name='Via administracion')
    frecuencia_horas = models.SmallIntegerField(db_column='frecuencia_horas', verbose_name='Frecuencia horas')
    duracion_dias = models.SmallIntegerField(db_column='duracion_dias', verbose_name='Duracion dias')
    cantidad_despachar = models.IntegerField(db_column='cantidad_despachar', verbose_name='Cantidad despachar')

    class Meta:
        managed = False
        db_table = 'DETALLE_RECETA'
        verbose_name = 'Detalles de receta'
        verbose_name_plural = 'Detalles de receta'

    def __str__(self):
        return f"Detalles de receta #{self.pk}"

class CatalogoExamen(models.Model):
    id_examen = models.AutoField(primary_key=True, db_column='id_examen', verbose_name='Id examen')
    nombre = models.CharField(max_length=100, unique=True, db_column='nombre', verbose_name='Nombre')
    tipo = models.CharField(max_length=12, db_column='tipo', verbose_name='Tipo')
    precio = models.DecimalField(max_digits=10, decimal_places=2, db_column='precio', verbose_name='Precio')

    class Meta:
        managed = False
        db_table = 'CATALOGO_EXAMEN'
        verbose_name = 'Catálogo de exámenes'
        verbose_name_plural = 'Catálogo de exámenes'

    def __str__(self):
        return str(self.nombre)

class OrdenExamen(models.Model):
    id_orden = models.AutoField(primary_key=True, db_column='id_orden', verbose_name='Id orden')
    id_consulta = models.ForeignKey('Consulta', on_delete=models.PROTECT, db_column='id_consulta', verbose_name='Id consulta')
    id_examen = models.ForeignKey('CatalogoExamen', on_delete=models.PROTECT, db_column='id_examen', verbose_name='Id examen')
    fecha_solicitud = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_solicitud', verbose_name='Fecha solicitud')
    estado = models.CharField(max_length=12, default='Solicitado', db_column='estado', verbose_name='Estado')
    resultado = models.CharField(max_length=500, null=True, blank=True, db_column='resultado', verbose_name='Resultado')

    class Meta:
        managed = False
        db_table = 'ORDEN_EXAMEN'
        verbose_name = 'Órdenes de examen'
        verbose_name_plural = 'Órdenes de examen'

    def __str__(self):
        return f"Órdenes de examen #{self.pk}"

class Procedimiento(models.Model):
    id_procedimiento = models.AutoField(primary_key=True, db_column='id_procedimiento', verbose_name='Id procedimiento')
    nombre = models.CharField(max_length=100, unique=True, db_column='nombre', verbose_name='Nombre')
    precio = models.DecimalField(max_digits=10, decimal_places=2, db_column='precio', verbose_name='Precio')

    class Meta:
        managed = False
        db_table = 'PROCEDIMIENTO'
        verbose_name = 'Procedimientos'
        verbose_name_plural = 'Procedimientos'

    def __str__(self):
        return str(self.nombre)

class Factura(models.Model):
    id_factura = models.AutoField(primary_key=True, db_column='id_factura', verbose_name='Id factura')
    numero_factura = models.CharField(max_length=20, unique=True, db_column='numero_factura', verbose_name='Numero factura')
    id_consulta = models.ForeignKey('Consulta', on_delete=models.PROTECT, db_column='id_consulta', verbose_name='Id consulta')
    id_poliza = models.ForeignKey('Poliza', on_delete=models.PROTECT, null=True, blank=True, db_column='id_poliza', verbose_name='Id poliza')
    fecha_emision = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_emision', verbose_name='Fecha emision')
    tipo = models.CharField(max_length=7, default='Total', db_column='tipo', verbose_name='Tipo')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, db_column='subtotal', verbose_name='Subtotal')
    deducible_aplicado = models.DecimalField(max_digits=12, decimal_places=2, default=0, db_column='deducible_aplicado', verbose_name='Deducible aplicado',
        validators=[MinValueValidator(0)], help_text='Importe a cargo del paciente antes de aplicar la cobertura. Añade primero los detalles de factura. La aseguradora cubre el porcentaje de la póliza sobre el subtotal menos este deducible.')
    monto_aseguradora = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, db_column='monto_aseguradora', verbose_name='Monto aseguradora')
    monto_paciente = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, db_column='monto_paciente', verbose_name='Monto paciente')
    estado_pago_paciente = models.CharField(max_length=10, default='Pendiente', db_column='estado_pago_paciente', verbose_name='Estado pago paciente')
    estado_cobro_aseguradora = models.CharField(max_length=10, default='NoAplica', db_column='estado_cobro_aseguradora', verbose_name='Estado cobro aseguradora')

    class Meta:
        managed = False
        db_table = 'FACTURA'
        verbose_name = 'Facturas'
        verbose_name_plural = 'Facturas'

    def __str__(self):
        return str(self.numero_factura)

    def clean(self):
        super().clean()
        errores = {}
        try:
            self.deducible_aplicado = self._meta.get_field('deducible_aplicado').clean(self.deducible_aplicado, self)
        except ValidationError as exc:
            raise ValidationError({'deducible_aplicado': exc.messages}) from exc
        if self.id_poliza_id and self.id_consulta_id:
            try:
                paciente_poliza = self.id_poliza.id_paciente_id
                paciente_consulta = self.id_consulta.id_cita.id_paciente_id
            except (Poliza.DoesNotExist, Consulta.DoesNotExist, Cita.DoesNotExist):
                # La validación del campo FK informa si no existe el registro.
                pass
            else:
                if paciente_poliza != paciente_consulta:
                    errores['id_poliza'] = 'La póliza debe pertenecer al paciente de la consulta.'
        if self.deducible_aplicado is not None:
            if not self.id_poliza_id and self.deducible_aplicado != 0:
                errores['deducible_aplicado'] = 'Sin póliza, el deducible aplicado debe ser cero.'
            elif self.subtotal is not None and self.deducible_aplicado > self.subtotal:
                errores['deducible_aplicado'] = 'El deducible no puede superar el subtotal de los detalles.'
        if errores:
            raise ValidationError(errores)

    def _calcular_totales(self, using, ajustar_deducible=False):
        try:
            self.deducible_aplicado = self._meta.get_field('deducible_aplicado').clean(self.deducible_aplicado, self)
        except ValidationError as exc:
            raise ValidationError({'deducible_aplicado': exc.messages}) from exc
        self.subtotal = (DetalleFactura.objects.using(using).filter(id_factura_id=self.pk)
                         .aggregate(total=Sum('subtotal_linea'))['total'] or Decimal('0.00')) if self.pk else Decimal('0.00')
        if ajustar_deducible:
            self.deducible_aplicado = min(self.deducible_aplicado, self.subtotal)
        cobertura = self.id_poliza.porcentaje_cobertura if self.id_poliza_id else Decimal('0')
        self.monto_aseguradora, self.monto_paciente = calcular_importes(
            self.subtotal, self.deducible_aplicado, cobertura)

    def save(self, *args, **kwargs):
        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and not update_fields:
            return
        kwargs['using'] = using
        with transaction.atomic(using=using):
            anterior = (type(self).objects.using(using).select_for_update().filter(pk=self.pk).first()
                        if self.pk else None)
            calculo = copy(self)
            calculo._state.db = using
            if anterior and update_fields is not None:
                # Los campos omitidos de update_fields conservan sus valores en SQL.
                for nombre in ('id_consulta', 'id_poliza', 'deducible_aplicado'):
                    campo = self._meta.get_field(nombre)
                    if nombre not in update_fields and campo.attname not in update_fields:
                        setattr(calculo, campo.attname, getattr(anterior, campo.attname))
            calculo._calcular_totales(using)
            calculo.clean()
            self.subtotal = calculo.subtotal
            self.monto_aseguradora = calculo.monto_aseguradora
            self.monto_paciente = calculo.monto_paciente
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'subtotal', 'monto_aseguradora', 'monto_paciente'}
            return super().save(*args, **kwargs)

    @classmethod
    def recalcular(cls, facturas, using):
        """Llamar dentro de una transacción y con las facturas bloqueadas."""
        for factura in facturas:
            factura._calcular_totales(using, ajustar_deducible=True)
            factura.clean()
            cls.objects.using(using).filter(pk=factura.pk).update(
                subtotal=factura.subtotal, deducible_aplicado=factura.deducible_aplicado,
                monto_aseguradora=factura.monto_aseguradora, monto_paciente=factura.monto_paciente)

class DetalleFactura(models.Model):
    id_detalle_factura = models.AutoField(primary_key=True, db_column='id_detalle_factura', verbose_name='Id detalle factura')
    id_factura = models.ForeignKey('Factura', on_delete=models.PROTECT, db_column='id_factura', verbose_name='Id factura')
    tipo_concepto = models.CharField(max_length=13, db_column='tipo_concepto', verbose_name='Tipo concepto')
    descripcion = models.CharField(max_length=200, db_column='descripcion', verbose_name='Descripcion')
    id_medicamento = models.ForeignKey('Medicamento', on_delete=models.PROTECT, null=True, blank=True, db_column='id_medicamento', verbose_name='Id medicamento')
    id_examen = models.ForeignKey('CatalogoExamen', on_delete=models.PROTECT, null=True, blank=True, db_column='id_examen', verbose_name='Id examen')
    id_procedimiento = models.ForeignKey('Procedimiento', on_delete=models.PROTECT, null=True, blank=True, db_column='id_procedimiento', verbose_name='Id procedimiento')
    cantidad = models.IntegerField(default=1, db_column='cantidad', verbose_name='Cantidad', validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, db_column='precio_unitario', verbose_name='Precio unitario', validators=[MinValueValidator(0)])
    subtotal_linea = models.DecimalField(max_digits=12, decimal_places=2, editable=False, db_column='subtotal_linea', verbose_name='Subtotal linea')

    class Meta:
        managed = False
        db_table = 'DETALLE_FACTURA'
        verbose_name = 'Detalles de factura'
        verbose_name_plural = 'Detalles de factura'

    def __str__(self):
        return f"Detalles de factura #{self.pk}"

    def clean(self):
        super().clean()
        if self.cantidad is not None and self.precio_unitario is not None:
            self.subtotal_linea = subtotal_de_linea(self.cantidad, self.precio_unitario)

    def save(self, *args, **kwargs):
        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and not update_fields:
            return
        kwargs['using'] = using
        with transaction.atomic(using=using):
            anterior = type(self).objects.using(using).filter(pk=self.pk).first() if self.pk else None
            calculo = copy(self)
            if anterior and update_fields is not None:
                for nombre in ('cantidad', 'precio_unitario', 'id_factura'):
                    campo = self._meta.get_field(nombre)
                    if nombre not in update_fields and campo.attname not in update_fields:
                        setattr(calculo, campo.attname, getattr(anterior, campo.attname))
            facturas_ids = {calculo.id_factura_id}
            if anterior:
                facturas_ids.add(anterior.id_factura_id)
            facturas = list(Factura.objects.using(using).select_for_update()
                            .filter(pk__in=facturas_ids).order_by('pk'))
            if anterior:
                actual = type(self).objects.using(using).get(pk=self.pk)
                if actual.id_factura_id != anterior.id_factura_id:
                    raise ValidationError('El detalle cambió de factura durante la edición. Recarga la página e inténtalo de nuevo.')
                if update_fields is not None:
                    for nombre in ('cantidad', 'precio_unitario', 'id_factura'):
                        campo = self._meta.get_field(nombre)
                        if nombre not in update_fields and campo.attname not in update_fields:
                            setattr(calculo, campo.attname, getattr(actual, campo.attname))
            calculo.clean()
            self.subtotal_linea = calculo.subtotal_linea
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'subtotal_linea'}
            resultado = super().save(*args, **kwargs)
            Factura.recalcular(facturas, using)
            return resultado

    def delete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=using):
            actual = type(self).objects.using(using).filter(pk=self.pk).first()
            facturas = list(Factura.objects.using(using).select_for_update()
                            .filter(pk=actual.id_factura_id if actual else self.id_factura_id))
            if actual:
                vigente = type(self).objects.using(using).filter(pk=self.pk).first()
                if vigente and vigente.id_factura_id != actual.id_factura_id:
                    raise ValidationError('El detalle cambió de factura durante la eliminación. Recarga la página e inténtalo de nuevo.')
            resultado = super().delete(using=using, keep_parents=keep_parents)
            Factura.recalcular(facturas, using)
            return resultado

class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True, db_column='id_pago', verbose_name='Id pago')
    id_factura = models.ForeignKey('Factura', on_delete=models.PROTECT, db_column='id_factura', verbose_name='Id factura')
    fecha_pago = models.DateTimeField(default=datetime.now, editable=False, db_column='fecha_pago', verbose_name='Fecha pago')
    monto = models.DecimalField(max_digits=12, decimal_places=2, db_column='monto', verbose_name='Monto')
    pagador = models.CharField(max_length=10, db_column='pagador', verbose_name='Pagador')
    metodo = models.CharField(max_length=15, db_column='metodo', verbose_name='Metodo')
    referencia = models.CharField(max_length=50, null=True, blank=True, db_column='referencia', verbose_name='Referencia')

    class Meta:
        managed = False
        db_table = 'PAGO'
        verbose_name = 'Pagos'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pagos #{self.pk}"

class AlergiaPaciente(models.Model):
    id_alergia = models.AutoField(primary_key=True, db_column='id_alergia', verbose_name='Id alergia')
    id_paciente = models.ForeignKey('Paciente', on_delete=models.PROTECT, db_column='id_paciente', verbose_name='Id paciente')
    id_componente = models.ForeignKey('ComponenteActivo', on_delete=models.PROTECT, db_column='id_componente', verbose_name='Id componente')
    reaccion = models.CharField(max_length=150, null=True, blank=True, db_column='reaccion', verbose_name='Reaccion')
    severidad = models.CharField(max_length=10, null=True, blank=True, db_column='severidad', verbose_name='Severidad')

    class Meta:
        managed = False
        db_table = 'ALERGIA_PACIENTE'
        verbose_name = 'Alergias por paciente'
        verbose_name_plural = 'Alergias por paciente'

    def __str__(self):
        return f"Alergias por paciente #{self.pk}"

