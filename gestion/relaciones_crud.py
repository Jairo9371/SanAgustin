"""CRUD para tablas puente SQL Server con PK compuesta.

La base original usa PK (columna1, columna2). Para no depender del soporte
parcial de claves compuestas del ORM/driver, ejecutamos SQL PARAMETRIZADO.
La tabla, sus columnas y los modelos disponibles provienen solo del catálogo
cerrado que define el código, jamás de la petición HTTP.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.db import connection, transaction, DataError, IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from django.shortcuts import redirect, render
from .catalogo import MODELOS, RELACIONES

# Tablas de origen para cada FK y campos complementarios permitidos.
CAMPOS_RELACION = {
    'paciente_condicion': {
        'id_paciente': 'paciente', 'id_condicion': 'condicion_cronica',
        'fecha_diagnostico': 'fecha', 'observaciones': 'texto_250',
    },
    'medico_subespecialidad': {
        'id_medico': 'medico', 'id_especialidad': 'especialidad',
    },
    'consulta_diagnostico': {
        'id_consulta': 'consulta', 'codigo_cie10': 'diagnostico_cie10',
        'tipo': 'texto_10_obligatorio',
    },
    'medicamento_componente': {
        'id_medicamento': 'medicamento', 'id_componente': 'componente_activo',
    },
    'consulta_procedimiento': {
        'id_consulta': 'consulta', 'id_procedimiento': 'procedimiento',
        'cantidad': 'cantidad',
    },
}


def configuracion(slug):
    if slug not in RELACIONES:
        raise Http404('Tabla de relación desconocida')
    return RELACIONES[slug]


def crear_formulario(slug, data=None, initial=None):
    campos = {}
    etiquetas = {
        'id_medicamento': 'Nombre del medicamento',
        'id_componente': 'Nombre del componente',
    } if slug == 'medicamento_componente' else {}
    for columna, tipo in CAMPOS_RELACION[slug].items():
        if tipo in MODELOS:
            modelo = MODELOS[tipo]
            campos[columna] = forms.ModelChoiceField(
                queryset=modelo.objects.all().order_by(modelo._meta.pk.name),
                label=etiquetas.get(columna, columna.replace('_', ' ').capitalize()),
                empty_label='Seleccione...',
                widget=forms.Select(attrs={'class': 'form-control'}),
            )
        elif tipo == 'fecha':
            campos[columna] = forms.DateField(required=False, label='Fecha de diagnóstico',
                input_formats=['%Y-%m-%d'], widget=forms.DateInput(
                    attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'))
        elif tipo in ('texto_250', 'texto_10_obligatorio'):
            campos[columna] = forms.CharField(
                required=tipo == 'texto_10_obligatorio',
                max_length=250 if tipo == 'texto_250' else 10,
                label=columna.replace('_', ' ').capitalize(),
                widget=forms.TextInput(attrs={'class': 'form-control'}))
        elif tipo == 'cantidad':
            campos[columna] = forms.IntegerField(min_value=1, max_value=2147483647, initial=1,
                label='Cantidad', widget=forms.NumberInput(
                    attrs={'class': 'form-control', 'min': 1, 'max': 2147483647}))
    Formulario = type('FormularioRelacion', (forms.Form,), campos)
    return Formulario(data=data, initial=initial)


def columnas_pk(slug):
    # Las primeras dos columnas son la PK, según el DDL suministrado.
    return RELACIONES[slug]['columnas'][:2]


def comillas(identificador):
    # Solo se usa con identificadores del catálogo, nunca entradas del usuario.
    if not identificador.replace('_', '').isalnum():
        raise ValueError('Identificador SQL inesperado')
    return f'[{identificador}]'


def claves_relacion(slug, clave_1, clave_2):
    """Validar las claves de la URL antes de enviarlas a SQL Server."""
    configuracion(slug)
    claves = []
    for columna, valor in zip(columnas_pk(slug), (clave_1, clave_2)):
        modelo = MODELOS[CAMPOS_RELACION[slug][columna]]
        campo = modelo._meta.pk
        try:
            valor = campo.to_python(valor)
            # El DDL existente usa INT, aunque un backend de pruebas admita 64 bits.
            if campo.get_internal_type() == 'AutoField' and not -2147483648 <= valor <= 2147483647:
                raise ValidationError('La clave supera el rango INT de SQL Server.')
            campo.run_validators(valor)
        except (ValidationError, TypeError, ValueError, OverflowError) as exc:
            raise Http404('Clave de relación no válida') from exc
        claves.append(valor)
    return claves


def fila_relacion(slug, clave_1, clave_2):
    item = configuracion(slug)
    cols = item['columnas']
    pk_a, pk_b = columnas_pk(slug)
    claves = claves_relacion(slug, clave_1, clave_2)
    sql = (f'SELECT {", ".join(map(comillas, cols))} FROM {comillas(item["tabla"])} '
           f'WHERE {comillas(pk_a)} = %s AND {comillas(pk_b)} = %s')
    with connection.cursor() as cursor:
        cursor.execute(sql, claves)
        fila = cursor.fetchone()
    if fila is None:
        raise Http404('No existe ese registro')
    return dict(zip(cols, fila))


def valores_formulario(slug, form):
    datos = {}
    for columna in RELACIONES[slug]['columnas']:
        valor = form.cleaned_data[columna]
        if hasattr(valor, '_meta'):  # ModelChoiceField devuelve una instancia del modelo.
            valor = valor.pk
        if valor == '' and columna == 'observaciones':
            valor = None
        datos[columna] = valor
    return datos


def solo_personal(user):
    return user.is_active and user.is_staff


@login_required
@user_passes_test(solo_personal)
def nueva_relacion(request, slug):
    item = configuracion(slug)
    formulario = crear_formulario(slug, data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and formulario.is_valid():
        datos = valores_formulario(slug, formulario)
        columnas = item['columnas']
        sentencia = (f'INSERT INTO {comillas(item["tabla"])} '
                     f'({", ".join(map(comillas, columnas))}) '
                     f'VALUES ({", ".join(["%s"] * len(columnas))})')
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(sentencia, [datos[col] for col in columnas])
        except IntegrityError:
            formulario.add_error(None, 'No se pudo crear la relación. Comprueba si ya existe.')
        except DataError:
            formulario.add_error(None, 'No se pudo crear la relación. Comprueba los valores y sus límites.')
        else:
            messages.success(request, 'Relación creada correctamente (INSERT).')
            return redirect('gestion:relaciones', slug=slug)
    return render(request, 'gestion/formulario_relacion.html', {
        'titulo': item['nombre'], 'slug': slug, 'accion': 'Crear', 'form': formulario,
    })


@login_required
@user_passes_test(solo_personal)
def editar_relacion(request, slug, pk1, pk2):
    item = configuracion(slug)
    existente = fila_relacion(slug, pk1, pk2)
    formulario = crear_formulario(slug,
        data=request.POST if request.method == 'POST' else None, initial=existente)
    if request.method == 'POST' and formulario.is_valid():
        datos = valores_formulario(slug, formulario)
        columnas = item['columnas']
        pk_a, pk_b = columnas_pk(slug)
        sentencia = (f'UPDATE {comillas(item["tabla"])} SET '
                     + ', '.join(f'{comillas(col)} = %s' for col in columnas)
                     + f' WHERE {comillas(pk_a)} = %s AND {comillas(pk_b)} = %s')
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(sentencia, [datos[col] for col in columnas]
                               + [existente[pk_a], existente[pk_b]])
        except IntegrityError:
            formulario.add_error(None, 'No se pudo actualizar. Comprueba la clave y las relaciones.')
        except DataError:
            formulario.add_error(None, 'No se pudo actualizar. Comprueba los valores y sus límites.')
        else:
            messages.success(request, 'Relación actualizada correctamente (UPDATE).')
            return redirect('gestion:relaciones', slug=slug)
    return render(request, 'gestion/formulario_relacion.html', {
        'titulo': item['nombre'], 'slug': slug, 'accion': 'Editar', 'form': formulario,
    })


@login_required
@user_passes_test(solo_personal)
def eliminar_relacion(request, slug, pk1, pk2):
    item = configuracion(slug)
    existente = fila_relacion(slug, pk1, pk2)
    if request.method == 'POST':
        pk_a, pk_b = columnas_pk(slug)
        sentencia = (f'DELETE FROM {comillas(item["tabla"])} '
                     f'WHERE {comillas(pk_a)} = %s AND {comillas(pk_b)} = %s')
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute(sentencia, [existente[pk_a], existente[pk_b]])
        except IntegrityError:
            messages.error(request, 'No se puede eliminar la relación por integridad referencial.')
        else:
            messages.success(request, 'Relación eliminada correctamente (DELETE).')
        return redirect('gestion:relaciones', slug=slug)
    return render(request, 'gestion/eliminar_relacion.html', {
        'titulo': item['nombre'], 'slug': slug, 'registro': existente,
    })
