from django.contrib import admin
from .models import (
    Categoria,
    Producto,
    ImagenProducto,
    Resena,
    RespuestaResena,
    ConfiguracionAgenda,
    FechaBloqueada,
    CupoFecha,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nombre', 'precio', 'categoria',
        'stock', 'porciones', 'ventas',
        'estado_producto', 'destacado', 'mas_vendido', 'es_nuevo',
    )
    list_filter = ('categoria', 'estado_producto', 'destacado', 'mas_vendido', 'es_nuevo')
    list_editable = ('precio', 'stock', 'porciones', 'ventas', 'estado_producto', 'destacado', 'mas_vendido', 'es_nuevo')
    search_fields = ('nombre', 'descripcion')
    list_per_page = 20


@admin.register(ImagenProducto)
class ImagenProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'imagen')
    search_fields = ('producto__nombre',)


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'usuario', 'calificacion')
    list_filter = ('calificacion',)
    search_fields = ('producto__nombre', 'usuario__username', 'comentario')


@admin.register(RespuestaResena)
class RespuestaResenaAdmin(admin.ModelAdmin):
    list_display = ('id', 'resena', 'usuario')
    search_fields = ('resena__producto__nombre', 'usuario__username')


@admin.register(ConfiguracionAgenda)
class ConfiguracionAgendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cupo_maximo_por_dia')


@admin.register(FechaBloqueada)
class FechaBloqueadaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'motivo')
    list_filter = ('fecha',)
    search_fields = ('motivo',)


@admin.register(CupoFecha)
class CupoFechaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'cupos_disponibles')
    list_filter = ('fecha',)