from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Producto, Categoria, Resena, RespuestaResena
from .forms import ResenaForm

def home(request):
    return render(request, 'home.html', {
        'destacados':  Producto.objects.filter(destacado=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True),
        'es_nuevos':      Producto.objects.filter(es_nuevo=True),
    }) 

def es_usuario(user):
    return user.is_authenticated and not user.is_staff


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

def home(request):
    return render(request, 'home.html', {
        'destacados':  Producto.objects.filter(destacado=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True),
        'es_nuevos':      Producto.objects.filter(es_nuevo=True),
    })


def es_usuario(user):
    return user.is_authenticated and not user.is_staff


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
    producto = get_object_or_404(
        Producto.objects.prefetch_related(
            'imagenes',
            'resenas__usuario',
            'resenas__respuestas__usuario'
        ),
        id=producto_id
    )

    resenas = producto.resenas.all().order_by('-fecha_creacion')
    resena_usuario = None
    form = None

    if request.user.is_authenticated:
        resena_usuario = resenas.filter(usuario=request.user).first()

        if request.method == 'POST':
            accion = request.POST.get('accion')

            # ---------- ACCIÓN: RESPONDER (solo staff) ----------
            if accion == 'responder':
                if not request.user.is_staff:
                    messages.error(request, 'No tienes permiso para responder reseñas.')
                    return redirect('producto_detalle', producto_id=producto.id)

                resena_id = request.POST.get('resena_id')
                texto = request.POST.get('respuesta', '').strip()

                if not texto:
                    messages.error(request, 'La respuesta no puede estar vacía.')
                    return redirect('producto_detalle', producto_id=producto.id)

                resena = get_object_or_404(Resena, id=resena_id, producto=producto)

                RespuestaResena.objects.create(
                    resena=resena,
                    usuario=request.user,
                    respuesta=texto
                )
                messages.success(request, 'Respuesta publicada correctamente.')
                return redirect('producto_detalle', producto_id=producto.id)

            # ---------- ACCIÓN: ELIMINAR reseña propia ----------
            if accion == 'eliminar' and resena_usuario:
                resena_usuario.delete()
                messages.success(request, 'Tu reseña ha sido eliminada.')
                return redirect('producto_detalle', producto_id=producto.id)

            # ---------- ACCIÓN: GUARDAR / EDITAR reseña ----------
            if accion == 'guardar':
                form = ResenaForm(request.POST, instance=resena_usuario)
                if form.is_valid():
                    resena = form.save(commit=False)
                    resena.producto = producto
                    resena.usuario = request.user
                    resena.save()

                    mensaje = 'Reseña actualizada.' if resena_usuario else 'Reseña publicada. ¡Gracias!'
                    messages.success(request, mensaje)
                    return redirect('producto_detalle', producto_id=producto.id)
        else:
            # Si el usuario es staff, no mostramos el formulario de reseña
            if not request.user.is_staff:
                form = ResenaForm(instance=resena_usuario)

    contexto = {
        'producto': producto,
        'resenas': resenas,
        'resena_usuario': resena_usuario,
        'form': form,
    }
    return render(request, 'detalle_producto.html', contexto)
    