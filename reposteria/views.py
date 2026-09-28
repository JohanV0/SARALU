from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Producto
from .forms import ProductoForm


def home(request):
    """Home que muestra productos destacados, más vendidos y nuevos."""
    return render(request, 'home.html', {
        'destacados': Producto.objects.filter(destacado=True, estado_producto=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True, estado_producto=True),
        'nuevos': Producto.objects.filter(es_nuevo=True, estado_producto=True),
    })


@staff_member_required
def registrar_producto(request):
    """HU-009: Registrar producto (solo dueña)."""
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'¡{producto.nombre} registrado correctamente!')
            return redirect('lista_productos')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm()

    return render(request, 'registrar_producto.html', {'form': form})


@staff_member_required
def lista_productos(request):
    """HU-016: Lista de todos los productos para modificar."""
    productos = Producto.objects.all().order_by('-fecha_creacion')
    return render(request, 'lista_productos.html', {'productos': productos})


@staff_member_required
def editar_producto(request, producto_id):
    """HU-016: Modificar producto existente."""
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡{producto.nombre} actualizado correctamente!')
            return redirect('lista_productos')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'editar_producto.html', {
        'form': form,
        'producto': producto,
    })


def catalogo(request):
    """Catálogo público de productos."""
    productos = Producto.objects.filter(estado_producto=True).order_by('-fecha_creacion')
    return render(request, 'catalogo.html', {'productos': productos})