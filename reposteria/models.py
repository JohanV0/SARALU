from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    porciones = models.PositiveIntegerField()
    imagen = models.ImageField(
        upload_to='productos/',
        blank=True,
        null=True
    )
    disponible = models.BooleanField(default=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class Resena(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='resenas'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='resenas'
    )

    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.usuario.nombre}" 

class RespuestaResena(models.Model):
    resena = models.OneToOneField(
        Resena,
        on_delete=models.CASCADE,
        related_name='respuesta'
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='respuestas_resenas'
    )

    respuesta = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Respuesta a reseña #{self.resena.id}" 

class ConfiguracionAgenda(models.Model):
    pedidos_maximos_dia = models.PositiveIntegerField(default=5)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"Cupo diario: {self.pedidos_maximos_dia}" 

class FechaAgenda(models.Model):
    fecha = models.DateField(unique=True)
    bloqueada = models.BooleanField(default=False)
    cupo_maximo = models.PositiveIntegerField()
    cupos_utilizados = models.PositiveIntegerField(default=0)

    def cupos_disponibles(self):
        return self.cupo_maximo - self.cupos_utilizados

    def tiene_cupo(self):
        return (
            not self.bloqueada
            and self.cupos_disponibles() > 0
        )

    def __str__(self):
        return str(self.fecha)

class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado'),
        ('PREPARACION', 'En preparación'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]

    TIPOS_ENTREGA = [
        ('DOMICILIO', 'Domicilio'),
        ('RECOJO', 'Recojo'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos'
    )

    fecha_pedido = models.DateTimeField(auto_now_add=True)

    fecha_entrega = models.ForeignKey(
        FechaAgenda,
        on_delete=models.PROTECT,
        related_name='pedidos'
    )

    hora_entrega = models.TimeField()

    tipo_entrega = models.CharField(
        max_length=20,
        choices=TIPOS_ENTREGA
    )

    nombre_cliente = models.CharField(max_length=100)
    telefono_cliente = models.CharField(max_length=20)
    direccion = models.CharField(max_length=250, blank=True)
    comentarios = models.TextField(blank=True)

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    def __str__(self):
        return f"Pedido #{self.id}" 
class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT
    )

    cantidad = models.PositiveIntegerField(default=1)

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}" 

class FotoPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='fotos'
    )

    imagen = models.ImageField(
        upload_to='pedidos/referencias/'
    )

    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto del pedido #{self.pedido.id}" 
