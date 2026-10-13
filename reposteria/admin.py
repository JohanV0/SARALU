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
    # HorarioAtencion,   ← comentado, no existe
    # Perfil,            ← comentado, no existe
    # DireccionCliente,  ← comentado, no existe
    # Carrito,           ← comentado, no existe
    # ItemCarrito,       ← comentado, no existe
    # Favorito,          ← comentado, no existe
    # Cupon,             ← comentado, no existe
    # Pedido,            ← comentado, no existe
    # DetallePedido,     ← comentado, no existe
    # HistorialEstadoPedido,  ← comentado
    # Pago,              ← comentado, no existe
    # Notificacion,      ← comentado, no existe
)

admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(ImagenProducto)
admin.site.register(Resena)
admin.site.register(RespuestaResena)
admin.site.register(ConfiguracionAgenda)
admin.site.register(FechaBloqueada)
admin.site.register(CupoFecha)
# admin.site.register(HorarioAtencion)   ← comentado
# admin.site.register(Perfil)            ← comentado
# admin.site.register(DireccionCliente)  ← comentado
# admin.site.register(Carrito)           ← comentado
# admin.site.register(ItemCarrito)       ← comentado
# admin.site.register(Favorito)          ← comentado
# admin.site.register(Cupon)             ← comentado
# admin.site.register(Pedido)            ← comentado
# admin.site.register(DetallePedido)     ← comentado
# admin.site.register(HistorialEstadoPedido)  ← comentado
# admin.site.register(Pago)              ← comentado
# admin.site.register(Notificacion)      ← comentado