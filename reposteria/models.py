from django.db import models

class Categoria(models.Model):
    '''
    modelo que representa las categorias
    '''
    nombre = models.CharField(max_length=100)
    imagenPrincipal = models.ImageField(upload_to = 'img/', default = 'img/logo.png')

    def __str__(self):
        return self.nombre  

class Producto(models.Model):
    '''
    modelo que represento un producto
    '''
        # relacion 1 a muchos: una categoria tiene muchos productos
    categoria = models.ForeignKey(
        Categoria,
        on_delete = models.CASCADE,
        related_name='productos',
    )
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2)

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
        return f"Imagen del producto: {self.producto.name}"

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
        return f'{self.usuario.username} respondio la resena de {self.resena.producto.username}'

class ConfiguracionAgenda(models.Model):
    '''
    modelo que representa 
    '''
    