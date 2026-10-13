from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('productos/registrar/', views.registrar_producto, name='registrar_producto'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('calendario/', views.calendario_cliente, name='calendario'),
    
]