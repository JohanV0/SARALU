from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'destacado', 'mas_vendido', 'nuevo', 'imagen')
    list_filter = ('destacado', 'mas_vendido', 'nuevo')
    search_fields = ('nombre',)