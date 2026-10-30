from django import template
register = template.Library()

@register.filter
def campo(obj, nombre):
    valor = getattr(obj, nombre, None)
    if valor is None or valor == '':
        return '—'
    if isinstance(valor, bool):
        return 'Sí' if valor else 'No'
    return valor
