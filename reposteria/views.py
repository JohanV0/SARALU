from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Producto, Categoria


def home(request):
    return render(request, 'home.html')

def catalogo_view(request):
    categoria_id = request.GET.get('categoria')
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    categorias = Categoria.objects.all()

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    contexto = {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': int(categoria_id) if categoria_id else None,
    }
    return render(request, 'catalogo.html', contexto)