"""Cálculos monetarios de facturas, con redondeo a centavos."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError


CENTAVO = Decimal('0.01')
MAXIMO_IMPORTE = Decimal('9999999999.99')  # DECIMAL(12,2) del DDL.


def subtotal_de_linea(cantidad, precio_unitario):
    try:
        cantidad = Decimal(str(cantidad))
        precio_unitario = Decimal(str(precio_unitario))
        if not cantidad.is_finite() or cantidad < 1 or cantidad != cantidad.to_integral_value() or cantidad > 2147483647:
            raise ValidationError({'cantidad': 'Ingresa una cantidad entera entre 1 y 2147483647.'})
        if not precio_unitario.is_finite() or not 0 <= precio_unitario <= Decimal('99999999.99'):
            raise ValidationError({'precio_unitario': 'Ingresa un precio entre 0 y 99999999.99.'})
        if precio_unitario != precio_unitario.quantize(CENTAVO):
            raise ValidationError({'precio_unitario': 'El precio admite como máximo dos decimales.'})
        subtotal = cantidad * precio_unitario
        if subtotal > MAXIMO_IMPORTE:
            raise ValidationError('El subtotal de la línea supera el máximo permitido (9999999999.99).')
        return subtotal.quantize(CENTAVO, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError('La cantidad y el precio deben ser números válidos.') from exc


def calcular_importes(subtotal, deducible, cobertura):
    """El paciente asume el deducible; la cobertura se aplica al resto."""
    try:
        subtotal, deducible, cobertura = (Decimal(str(valor)) for valor in (subtotal, deducible, cobertura))
        if any(not valor.is_finite() for valor in (subtotal, deducible, cobertura)):
            raise ValidationError('Los importes deben ser números finitos.')
        if not 0 <= subtotal <= MAXIMO_IMPORTE:
            raise ValidationError('El subtotal de la factura supera el rango permitido (0 a 9999999999.99).')
        if not 0 <= deducible <= subtotal:
            raise ValidationError({'deducible_aplicado': 'El deducible debe estar entre cero y el subtotal.'})
        if not 0 <= cobertura <= 100:
            raise ValidationError('El porcentaje de cobertura de la póliza debe estar entre 0 y 100.')
        monto_aseguradora = ((subtotal - deducible) * cobertura / 100).quantize(CENTAVO, rounding=ROUND_HALF_UP)
        return monto_aseguradora, (subtotal - monto_aseguradora).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError('Los importes de la factura no son válidos.') from exc
