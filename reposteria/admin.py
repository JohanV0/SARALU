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
    # DetallePedido, # Descomenta si usas el modelo
    # Pedido,        # Descomenta si usas el modelo
)

# Registro directo de cada modelo en el panel de administración
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(ImagenProducto)
admin.site.register(Resena)
admin.site.register(RespuestaResena)
admin.site.register(ConfiguracionAgenda)
admin.site.register(FechaBloqueada)
admin.site.register(CupoFecha)

# Si decides activar los modelos de Pedido y DetallePedido en models.py, descomenta estas líneas:
# admin.site.register(Pedido)
# admin.site.register(DetallePedido)