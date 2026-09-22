from django.shortcuts import render , redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Producto

def home(request):
    return render(request, 'home.html', {
        'destacados':  Producto.objects.filter(destacado=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True),
        'nuevos':      Producto.objects.filter(nuevo=True),
    }) 