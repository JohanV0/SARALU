from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Producto, Categoria
from .forms import ResenaForm


def home(request):
    return render(request, 'home.html')

def catalogo_view(request):
    categoria_id = request.GET.get('categoria')
    productos = Producto.objects.select_related('categoria').prefetch_related('imagenes')
    categorias = Categoria.objects.all()

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    contexto = {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': int(categoria_id) if categoria_id else None,
    }
    return render(request, 'catalogo.html', contexto)

def detalle_producto_view(request, producto_id):
    producto = get_object_or_404(Producto.objects.prefetch_related('imagenes'), id=producto_id)
    return render(request, 'detalle_producto.html', {'producto': producto})

def detalle_producto_view(request, producto_id):
    # Pre-cargamos imágenes y reseñas (con sus usuarios) para optimizar
    producto = get_object_or_404(Producto.objects.prefetch_related('imagenes', 'resenas__usuario'), id=producto_id)
    
    resenas = producto.resenas.all()
    resena_usuario = None
    form = None

    # CRITERIOS DE ACEPTACIÓN: Comportamiento según la sesión y estado
    if request.user.is_authenticated:
        # Buscamos si este usuario ya tiene una reseña en este producto
        resena_usuario = resenas.filter(usuario=request.user).first()
        
        if request.method == 'POST':
            accion = request.POST.get('accion')
            
            # Tarea: Eliminar reseña
            if accion == 'eliminar' and resena_usuario:
                resena_usuario.delete()
                messages.success(request, 'Tu reseña ha sido eliminada.')
                return redirect('detalle_producto', producto_id=producto.id)
            
            # Tarea: Crear o Editar reseña
            form = ResenaForm(request.POST, instance=resena_usuario)
            if form.is_valid():
                resena = form.save(commit=False) # Guardado temporal
                resena.producto = producto       # Le asignamos el producto actual
                resena.usuario = request.user    # Le asignamos el usuario actual
                resena.save()                    # Guardado final
                
                mensaje = 'Reseña actualizada.' if resena_usuario else 'Reseña publicada. ¡Gracias!'
                messages.success(request, mensaje)
                return redirect('detalle_producto', producto_id=producto.id)
        else:
            # Si es GET, mostramos el formulario (vacío o lleno si ya había reseña)
            form = ResenaForm(instance=resena_usuario)

    contexto = {
        'producto': producto,
        'resenas': resenas,
        'resena_usuario': resena_usuario,
        'form': form,
    }
    return render(request, 'detalle_producto.html', contexto)