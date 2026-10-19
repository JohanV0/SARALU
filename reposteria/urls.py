from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo_view, name='catalogo'),
    path('catalogo/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('producto/<int:producto_id>/', views.detalle_producto_view, name='producto_detalle'),
    path('catalogo/nuevo/', views.nuevo_producto, name='nuevo_producto'),
]