from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalogo_view, name='catalogo'),
    path('catalogo/nuevo/', views.nuevo_producto, name='nuevo_producto'),
    path('catalogo/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('producto/<int:producto_id>/', views.detalle_producto_view, name='producto_detalle'),
    path('producto/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('carrito/', views.ver_carrito_view, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('armar-pedido/', views.armar_pedido_view, name='armar_pedido'),
    path('lista_productos/', views.lista_productos, name = 'lista_productos'),
    path('lista_productos/<int:producto_id>/avanzar',views.avanzar_estado_categoria, name='avanzar_estado_categoria'),

]