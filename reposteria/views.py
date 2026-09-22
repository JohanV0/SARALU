from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Producto
from .forms import ProductoForm


def home(request):
    """Home temporal que redirige al formulario."""
    return redirect('registrar_producto')


@staff_member_required
def registrar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'¡{producto.nombre} registrado correctamente!')
            return redirect('registrar_producto')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm()

    productos = Producto.objects.all().order_by('-fecha_creacion')

    return render(request, 'registrar_producto.html', {
        'form': form,
        'productos': productos,
    })


def catalogo(request):
    productos = Producto.objects.filter(disponible=True).order_by('-fecha_creacion')
    return render(request, 'catalogo.html', {'productos': productos})