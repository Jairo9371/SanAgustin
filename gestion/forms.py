"""Formularios de las tablas SQL Server con PK simple."""
from django import forms
from django.core.validators import EmailValidator, RegexValidator, MinValueValidator, MaxValueValidator
from django.forms import modelform_factory


class FechaHoraInput(forms.DateTimeInput):
    supports_microseconds = True


class HoraInput(forms.TimeInput):
    supports_microseconds = True


class EstiloFormulario(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs['class'] = 'form-check-input'
            else:
                campo.widget.attrs['class'] = 'form-control'
            if isinstance(campo, forms.DateField) and not isinstance(campo, forms.DateTimeField):
                campo.widget = forms.DateInput(
                    attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d')
                campo.input_formats = ['%Y-%m-%d']
            elif isinstance(campo, forms.DateTimeField):
                campo.widget = FechaHoraInput(
                    attrs={'class': 'form-control', 'type': 'datetime-local', 'step': 'any'},
                    format='%Y-%m-%dT%H:%M:%S.%f')
                campo.input_formats = [
                    '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S',
                ]
            elif isinstance(campo, forms.TimeField):
                campo.widget = HoraInput(
                    attrs={'class': 'form-control', 'type': 'time', 'step': 'any'},
                    format='%H:%M:%S.%f')
                campo.input_formats = ['%H:%M:%S.%f', '%H:%M:%S', '%H:%M']

            if nombre == 'correo':
                campo.validators.append(EmailValidator(message='Ingresa un correo electrónico válido.'))
            if nombre == 'dpi':
                campo.validators.append(RegexValidator(
                    regex=r'^[0-9]{13}$', message='El DPI debe tener 13 dígitos numéricos.'))
            if nombre == 'porcentaje_cobertura':
                campo.validators.extend([MinValueValidator(0), MaxValueValidator(100)])

        # Si la PK no es IDENTITY (p. ej. codigo_cie10), impedir que la
        # edición de la PK genere accidentalmente un segundo registro.
        nombre_pk = self.instance._meta.pk.name
        if not self.instance._state.adding and nombre_pk in self.fields:
            self.fields[nombre_pk].disabled = True

    def clean(self):
        datos = super().clean()
        if ('fecha_inicio' in datos and 'fecha_fin' in datos
                and datos.get('fecha_fin') and datos['fecha_fin'] < datos['fecha_inicio']):
            self.add_error('fecha_fin', 'La fecha final no puede ser anterior a la inicial.')
        if ('hora_inicio' in datos and 'hora_fin' in datos
                and datos['hora_fin'] <= datos['hora_inicio']):
            self.add_error('hora_fin', 'La hora final debe ser posterior a la inicial.')
        return datos


def formulario_para(modelo):
    # Modelo declarado en el catálogo: no se construyen clases desde la URL.
    # Django excluye AutoField y campos marcados editable=False.
    return modelform_factory(modelo, form=EstiloFormulario, fields='__all__')
