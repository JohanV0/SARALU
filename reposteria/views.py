from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Producto, Categoria, Resena, RespuestaResena, Carrito, Pedido, DetallePedido, ItemCarrito
from .forms import ResenaForm

def home(request):
    return render(request, 'home.html', {
        'destacados':  Producto.objects.filter(destacado=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True),
        'es_nuevos':      Producto.objects.filter(es_nuevo=True),
    })


def es_usuario(user):
    return user.is_authenticated and not user.is_staff

def admin(user):
    return user.is_authenticated and user.is_staff

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
    productos_relacionados = (
        Producto.objects
        .filter(categoria=producto.categoria)     # misma categoría
        .exclude(id=producto.id)                   # sin el actual
        .order_by('-id')[:4]                       # opcional: los 4 más nuevos
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
        'productos_relacionados' : productos_relacionados,
        'producto': producto,
        'resenas': resenas,
        'resena_usuario': resena_usuario,
        'form': form,
    }
    return render(request, 'detalle_producto.html', contexto)
  
@login_required
def eliminar_producto(request,producto_id):
    producto = Producto.objects.get(id=producto_id)
    producto.delete()
    return redirect('catalogo')

@login_required
@user_passes_test(admin)
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        porciones = request.POST.get("porciones")
        ventas = request.POST.get("ventas")
        categoria_id = request.POST.get("categoria")
        estado = request.POST.get("estado")  # 'DISPONIBLE' o 'AGOTADO'
        
        # Leemos los checkboxes correctamente según el HTML
        destacado = 'destacado' in request.POST
        mas_vendido = 'mas_vendido' in request.POST
        es_nuevo = 'es_nuevo' in request.POST

        if not (nombre and precio and stock and porciones and categoria_id):
            messages.error(request, "Faltan campos obligatorios.")
            return render(request, "editar_producto.html", {
                "producto": producto,
                "categorias": categorias,
            })

        # Asignamos los valores al producto
        producto.nombre = nombre
        producto.descripcion = descripcion or ""
        producto.precio = float(precio)
        producto.stock = int(stock)
        producto.porciones = int(porciones)
        producto.ventas = int(ventas) if ventas else 0
        
        # CORRECCIÓN AQUÍ: estado en vez de estado_activo
        producto.estado = estado if estado else 'DISPONIBLE'
        
        producto.destacado = destacado
        producto.mas_vendido = mas_vendido
        producto.es_nuevo = es_nuevo
        
        if categoria_id:
            producto.categoria = get_object_or_404(Categoria, id=categoria_id)

        # Guardamos la imagen si se subió una nueva
        if request.FILES.get('imagen'):
            producto.imagen = request.FILES['imagen']

        producto.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("producto_detalle", producto_id=producto.id)

    # CORRECCIÓN AQUÍ: nombre del archivo con guion bajo
    return render(request, "editar-producto.html", {
        "producto": producto,
        "categorias": categorias,
    })
  
def nuevo_producto(request):
  categorias = Categoria.objects.all()

  if request.method == "POST":
    nombre = request.POST.get('nombre')
    descripcion = request.POST.get('descripcion')
    precio = request.POST.get('precio')
    categoria_id = request.POST.get('categoria')
    imagen = request.FILES.get('imagen')
    stock = request.POST.get('stock')
    porciones = request.POST.get('porciones')
    destacado = request.POST.get('destacado') == 'on'
    mas_vendido = request.POST.get('mas_vendido') == 'on'
    es_nuevo = request.POST.get('es_nuevo') == 'on'

    if nombre and descripcion and precio:
      producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        imagen=imagen,
        stock=int(stock) if stock else 10,
        porciones=int(porciones) if porciones else 1,
        destacado=destacado,
        mas_vendido=mas_vendido,
        es_nuevo=es_nuevo,
        categoria_id=categoria_id if categoria_id else None,
      )
      producto.save()

      messages.success(request, f'Producto "{producto.nombre}" registrado correctamente.')
      return redirect('catalogo')

  return render(request, 'nuevo-producto.html', {'categorias': categorias})

@login_required
@user_passes_test(admin)
def lista_productos(request):
    productos = Producto.objects.all()
    return render(request,'lista_productos.html',{"productos":productos})

@login_required
def armar_pedido_view(request):
    # 1. Buscamos el carrito del usuario actual
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    items_carrito = carrito.items.all()

    # CRITERIO 2: Si el carrito está vacío, rebota al catálogo
    if not items_carrito.exists():
        messages.warning(request, "Debes elegir al menos un producto para armar un pedido.")
        return redirect('catalogo')

    # CRITERIO 1: Calculamos el total
    subtotal = sum(item.subtotal() for item in items_carrito)

    # PASO 3: GUARDAR EL PEDIDO CUANDO SE ENVÍA EL FORMULARIO
    if request.method == 'POST':
        tipo_entrega = request.POST.get('tipo_entrega')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        
        nota_horario = f"Fecha de entrega: {fecha} | Hora: {hora}"

        # Acción 1: Creamos el Pedido oficial
        nuevo_pedido = Pedido.objects.create(
            cliente=request.user,
            nombre_contacto=request.user.username, 
            telefono_contacto="", 
            domicilio=tipo_entrega,
            subtotal=subtotal,
            total=subtotal,
            comentarios=nota_horario
        )

        # Acción 2: Copiamos los items del carrito al pedido
        for item in items_carrito:
            DetallePedido.objects.create(
                pedido=nuevo_pedido,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio
            )

        # Acción 3: Vaciamos el carrito (borramos los items)
        items_carrito.delete()

        # Acción 4: Mensaje de éxito y lo mandamos al inicio
        messages.success(request, f"¡Tu pedido #{nuevo_pedido.id} ha sido confirmado con éxito!")
        return redirect('home')
    
    contexto = {
        'items': items_carrito,
        'subtotal': subtotal,
    }
    return render(request, 'armar_pedido.html', contexto)

@login_required
def ver_carrito_view(request):
    # Buscamos el carrito del usuario
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito.items.all()
    
    # CRITERIO 2: Calculamos el total acumulado
    total = sum(item.subtotal() for item in items)
    
    contexto = {
        'items': items,
        'total': total
    }
    # CRITERIO 1 y 3 se resolverán en el HTML (carrito.html)
    return render(request, 'carrito.html', contexto)

@login_required
def eliminar_item_carrito(request, item_id):
    # CRITERIO 4: Eliminar un producto del carrito
    # Buscamos el item asegurándonos que pertenezca al carrito de este usuario por seguridad
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    nombre_producto = item.producto.nombre
    item.delete()
    
    messages.success(request, f"Eliminaste {nombre_producto} de tu carrito.")
    return redirect('ver_carrito')

@require_POST
@login_required
def agregar_al_carrito(request, producto_id):
    # Función extra para que dejes de usar el administrador de Django
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    
    # Revisamos si el postre ya está en el carrito
    item, creado = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
    
    if not creado:
        # Si ya estaba, le sumamos 1 a la cantidad
        item.cantidad += 1
        item.save()
        
    messages.success(request, f"¡{producto.nombre} agregado al carrito!")
    # Lo mandamos a ver su carrito
    return redirect('ver_carrito')

def avanzar_estado_categoria(request, producto_id):
    categorias = get_object_or_404(Producto, id=producto_id)

    if categorias.estado == 'DISPONIBLE':
        categorias.estado = 'AGOTADO'
        categorias.save()
    elif categorias.estado == 'AGOTADO':
        categorias.estado = 'DISPONIBLE'
        categorias.save()
    
    
    return redirect('lista_productos')