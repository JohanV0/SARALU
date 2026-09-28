from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Categoria(models.Model):
    '''
    modelo que representa las categorias
    '''
    nombre = models.CharField(max_length=100)
    imagenPrincipal = models.ImageField(upload_to = 'img/', default = 'img/logo.png')

    def __str__(self):
        return self.nombre  

class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=10)
    estado_producto = models.BooleanField(default=True)
    porciones = models.PositiveIntegerField(default=1)
    destacado = models.BooleanField(default=False)
    mas_vendido = models.BooleanField(default=False)
    es_nuevo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ventas = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre

class ImagenProducto(models.Model):
    '''
    modelo que representa las imagenes de un producto
    '''
    # relacion 1 a muchos: un producto tiene muchas imagenes 
    producto = models.ForeignKey(
        Producto,
        on_delete= models.CASCADE,
        related_name='imagenes'
    )
    imagen = models.ImageField(upload_to = 'img/')

    def __str__(self):
        return f"Imagen del producto: {self.producto.nombre}"

class Resena(models.Model):
    '''
    modelo que representa una resena
    '''
        # relacion 1 a muchos: un producto puede tener muchas resenas 
    producto = models.ForeignKey(
        Producto,
        on_delete= models.CASCADE,
        related_name= 'resenas'
    )
        # relacion 1 a muchos: un usuario puede dejar varias resenas
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete= models.CASCADE,
        related_name= 'resenas'
    )
    comentario = models.TextField()
    calificacion = models.PositiveSmallIntegerField(
        validators = [
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    
    def __str__(self):
        return f'el usuario {self.usuario.username} califico el producto {self.producto.nombre}'

class RepuestaResena(models.Model):
    '''
    modelo que respresenta una respuesta a una resena
    '''
    respuesta = models.TextField()
        # relacion 1 a muchos: la dueña puede dejar varias respuestas a una serena
    resena = models.ForeignKey(
        Resena,
        on_delete= models.CASCADE,
        related_name= 'respuestas'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete= models.CASCADE,
        related_name= 'respuestas'
    )

    def __str__(self):
        return f'{self.usuario.username} respondio la resena de {self.resena.producto.nombre}'

class ConfiguracionAgenda(models.Model):
    """
    Configuración global de la agenda.
    """

    cupo_maximo_por_dia = models.PositiveSmallIntegerField(default=5)
    
    # Cuando guardes, fuerza que el id sea 1 (así solo hay una fila)
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    # Método para obtener la configuración (la crea si no existe)
    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    # Cómo se muestra como texto
    def __str__(self):
        return f'Cupo máximo: {self.cupo_maximo_por_dia}'

class FechaBloqueada(models.Model):
    '''
    Representa la fecha en la que la dueña no recibe pedidos.
    '''
    fecha = models.DateField(unique=True)
    motivo = models.CharField(max_length=150
    )

    def __str__(self):
        return f'{self.fecha} - {self.motivo or "sin motivo"}'
class CupoFecha(models.Model):
    '''
    Representa los limites disponible por fecha 
    '''
    fecha = models.DateField(unique=True)
    cupos_disponibles = models.PositiveSmallIntegerField

    def __str__(self):
        return f'{self.fecha}-{self.cupos_disponibles} cupos diponibles'

class DetallePedido(models.Model):
    '''
    modelo que representa un producto dentro de un pedido
    '''
    producto = models.ForeignKey(
        Producto,
        on_delete= models.CASCADE,
        related_name = 'detalles'
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete= models.CASCADE,
        related_name= 'detalles'
    )

class Pedido(models.Model):
    '''
    
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
        on_delete= models.CASCADE,
        related_name='clientes',
        null=True,
    )

    nombre_contacto = models.CharField(max_length=150)
    telefono_contacto = models.CharField(max_length=15)
    direccion_entrega = models.CharField(max_length=250)
    domicilio = models.CharField(
        max_length=20,
        choices='TIPOS_ENTREGA',
        default='domicilio')
    # Fechas 
    creado = models.DateTimeField('Creado', auto_now_add=True)
    actualizado = models.DateTimeField('Actualizado', auto_now=True)
    
    estado = models.CharField(
        max_length=15,
        choices='ESTADOS',
        default='pendiente'
    )


    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)

    # Comentarios del cliente
    comentarios = models.TextField('Comentarios', blank=True)

    def __str__(self):
        return f'Pedido #{self.id} - {self.nombre_contacto}'

    def contar_total(self):
        total = sum(detalle.total) for detalle in self.detalles.all())