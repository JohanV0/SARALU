from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=10)
    disponible = models.BooleanField(default=True)

    porciones = models.PositiveIntegerField(default=1)
    ventas = models.PositiveIntegerField(default=0)

    destacado = models.BooleanField(default=False)
    mas_vendido = models.BooleanField(default=False)
    es_nuevo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']