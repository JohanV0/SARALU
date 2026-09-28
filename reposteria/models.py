from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


# =========================================================
# CATEGORÍAS Y PRODUCTOS
# =========================================================

class Categoria(models.Model):
    '''
    modelo que representa las categorias
    '''
    nombre = models.CharField(max_length=100)
    imagen_principal = models.ImageField(upload_to='img/', default='img/logo.png')

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=10)
    estado_producto = models.BooleanField(default=True)
    porciones = models.PositiveIntegerField(default=1)
    destacado = models.BooleanField(default=False)
    mas_vendido = models.BooleanField(default=False)
    es_nuevo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ventas = models.PositiveIntegerField(default=0)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )

    def __str__(self):
        return self.nombre


class ImagenProducto(models.Model):
    '''
    modelo que representa las imagenes de un producto
    '''
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='imagenes'
    )
    imagen = models.ImageField(upload_to='img/')

    def __str__(self):
        return f"Imagen del producto: {self.producto.nombre}"


# =========================================================
# RESEÑAS
# =========================================================

class Resena(models.Model):
    '''
    modelo que representa una resena
    '''
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='resenas'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resenas'
    )
    comentario = models.TextField()
    calificacion = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'el usuario {self.usuario.username} califico el producto {self.producto.nombre}'


class RespuestaResena(models.Model):
    '''
    modelo que representa una respuesta a una resena
    '''
    respuesta = models.TextField()
    resena = models.ForeignKey(
        Resena,
        on_delete=models.CASCADE,
        related_name='respuestas'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='respuestas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.username} respondio la resena de {self.resena.producto.nombre}'


# =========================================================
# AGENDA / CUPOS / HORARIOS
# =========================================================

class ConfiguracionAgenda(models.Model):
    '''
    Configuración global de la agenda.
    '''
    cupo_maximo_por_dia = models.PositiveSmallIntegerField(default=5)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f'Cupo máximo: {self.cupo_maximo_por_dia}'


class FechaBloqueada(models.Model):
    '''
    Representa la fecha en la que la dueña no recibe pedidos.
    '''
    fecha = models.DateField(unique=True)
    motivo = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f'{self.fecha} - {self.motivo or "sin motivo"}'


class CupoFecha(models.Model):
    '''
    Representa los limites disponible por fecha
    '''
    fecha = models.DateField(unique=True)
    cupos_disponibles = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.fecha} - {self.cupos_disponibles} cupos disponibles'


class HorarioAtencion(models.Model):
    '''
    Horario general de atención por día de la semana.
    '''
    DIAS = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    dia = models.PositiveSmallIntegerField(choices=DIAS, unique=True)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.get_dia_display()}: {self.hora_apertura} - {self.hora_cierre}'


# =========================================================
# PERFIL Y DIRECCIONES
# =========================================================

class Perfil(models.Model):
    '''
    Datos extra del usuario.
    '''
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    telefono = models.CharField(max_length=15, blank=True)
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'Perfil de {self.usuario.username}'


class DireccionCliente(models.Model):
    '''
    Direcciones guardadas por el cliente.
    '''
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='direcciones'
    )
    alias = models.CharField(max_length=50, blank=True)  # "Casa", "Trabajo"
    direccion = models.CharField(max_length=250)
    barrio = models.CharField(max_length=100, blank=True)
    referencia = models.TextField(blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    principal = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Si se marca como principal, desmarca las demás del mismo usuario
        if self.principal:
            DireccionCliente.objects.filter(
                usuario=self.usuario, principal=True
            ).exclude(pk=self.pk).update(principal=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.alias or self.direccion} - {self.usuario.username}'


# =========================================================
# CARRITO
# =========================================================

class Carrito(models.Model):
    '''
    Carrito persistente por usuario.
    '''
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito'
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Carrito de {self.usuario.username}'


class ItemCarrito(models.Model):
    '''
    Producto dentro del carrito.
    '''
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='items_carrito'
    )
    cantidad = models.PositiveSmallIntegerField(default=1)

    def subtotal(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'


# =========================================================
# FAVORITOS
# =========================================================

class Favorito(models.Model):
    '''
    Productos marcados como favoritos por el usuario.
    '''
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favoritos'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='favoritos'
    )
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.username} ❤ {self.producto.nombre}'


# =========================================================
# CUPONES
# =========================================================

class Cupon(models.Model):
    '''
    Cupón de descuento.
    '''
    codigo = models.CharField(max_length=30, unique=True)
    descuento_porcentaje = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    usos_maximos = models.PositiveIntegerField(default=1)
    usos = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.codigo} ({self.descuento_porcentaje}%)'


# =========================================================
# PEDIDOS
# =========================================================

class Pedido(models.Model):
    '''
    Representa un pedido realizado por un cliente.
    '''
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('preparacion', 'En preparación'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    TIPOS_ENTREGA = [
        ('domicilio', 'Domicilio en Ibagué'),
        ('recojo', 'Recojo en tienda'),
    ]

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='pedidos',
        null=True,
        blank=True,
    )

    nombre_contacto = models.CharField(max_length=150)
    telefono_contacto = models.CharField(max_length=15)
    direccion_entrega = models.CharField(max_length=250, blank=True)

    direccion = models.ForeignKey(
        DireccionCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos'
    )

    domicilio = models.CharField(
        max_length=20,
        choices=TIPOS_ENTREGA,
        default='domicilio'
    )

    creado = models.DateTimeField('Creado', auto_now_add=True)
    actualizado = models.DateTimeField('Actualizado', auto_now=True)

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='pendiente'
    )

    cupon = models.ForeignKey(
        Cupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos'
    )

    subtotal = models.DecimalField(
        'Subtotal',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    descuento = models.DecimalField(
        'Descuento',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    total = models.DecimalField(
        'Total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    comentarios = models.TextField('Comentarios', blank=True)

    def __str__(self):
        return f'Pedido #{self.id} - {self.nombre_contacto}'

    def contar_total(self):
        subtotal = sum(
            (detalle.subtotal() for detalle in self.detalles.all()),
            Decimal('0.00')
        )
        descuento = Decimal('0.00')
        if self.cupon and self.cupon.activo:
            descuento = (subtotal * self.cupon.descuento_porcentaje) / Decimal('100')

        self.subtotal = subtotal
        self.descuento = descuento
        self.total = subtotal - descuento
        self.save(update_fields=['subtotal', 'descuento', 'total'])
        return self.total


class DetallePedido(models.Model):
    '''
    modelo que representa un producto dentro de un pedido
    '''
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    cantidad = models.PositiveSmallIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.cantidad} - {self.producto.nombre}'

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)


class HistorialEstadoPedido(models.Model):
    '''
    Registro de cambios de estado de un pedido.
    '''
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    estado = models.CharField(max_length=15, choices=Pedido.ESTADOS)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cambios_estado'
    )

    def __str__(self):
        return f'{self.pedido.id} → {self.estado}'


# =========================================================
# PAGOS
# =========================================================

class Pago(models.Model):
    '''
    Registro del pago de un pedido.
    '''
    METODOS = [
        ('efectivo', 'Efectivo contra entrega'),
        ('transferencia', 'Transferencia bancaria'),
        ('nequi', 'Nequi'),
        ('daviplata', 'Daviplata'),
    ]
    ESTADOS_PAGO = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Rechazado'),
    ]

    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='pago'
    )
    metodo = models.CharField(max_length=20, choices=METODOS, default='efectivo')
    estado = models.CharField(max_length=15, choices=ESTADOS_PAGO, default='pendiente')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    referencia = models.CharField(max_length=100, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pago {self.pedido.id} - {self.get_metodo_display()}'


# =========================================================
# NOTIFICACIONES
# =========================================================

class Notificacion(models.Model):
    '''
    Notificaciones para usuarios.
    '''
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo