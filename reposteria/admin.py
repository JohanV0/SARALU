from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'porciones', 'ventas', 'disponible', 'destacado', 'mas_vendido', 'es_nuevo')
    list_filter = ('disponible', 'destacado', 'mas_vendido', 'es_nuevo')
    list_editable = ('precio', 'stock', 'porciones', 'ventas', 'disponible', 'destacado', 'mas_vendido', 'es_nuevo')