from django.http import HttpResponse
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('catalogo/', views.catalogo_view, name='catalogo'),
    path('producto/<int:producto_id>/', views.detalle_producto_view, name='detalle_producto')
]