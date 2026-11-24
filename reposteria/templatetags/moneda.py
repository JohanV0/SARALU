from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def formatear_cop(value):
    """
    Convierte un número a texto en pesos colombianos.
    Ejemplo: 12500 -> "$12.500"
    Se puede usar en vistas: from .templatetags.moneda import formatear_cop
    """
    try:
        numero = int(Decimal(value))
    except (TypeError, ValueError, InvalidOperation):
        return value
    return "$" + f"{numero:,}".replace(",", ".")


@register.filter
def cop(value):
    """Uso en plantillas: {% load moneda %} {{ producto.precio|cop }}"""
    return formatear_cop(value)