import re
from urllib.parse import quote 
from django.conf import settings  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Prefetch, Q, F
from .models import (
    Producto, Categoria, Resena, RespuestaResena, Carrito,
    Pedido, DetallePedido, ItemCarrito, FechaBloqueada,
    CupoFecha, ConfiguracionAgenda, HistorialEstadoPedido
)
from .forms import ResenaForm


def home(request):
    return render(request, 'home.html', {
        'destacados': Producto.objects.filter(destacado=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True),
        'es_nuevos': Producto.objects.filter(es_nuevo=True),
    })


def es_usuario(user):
    return user.is_authenticated and not user.is_staff


def admin(user):
    return user.is_authenticated and user.is_staff


def catalogo_view(request):
    categoria_code = request.GET.get('categoria')  # "TARTAS", "CUPCAKES", ...
    productos = Producto.objects.select_related('categoria').prefetch_related('imagenes')
    categorias = Categoria.objects.all()

    if categoria_code:
        productos = productos.filter(categoria__categoria=categoria_code)

    contexto = {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': categoria_code,
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
        .filter(categoria=producto.categoria)  # misma categoría
        .exclude(id=producto.id)               # sin el actual
        .order_by('-id')[:4]                   # los 4 más nuevos
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
        'productos_relacionados': productos_relacionados,
        'producto': producto,
        'resenas': resenas,
        'resena_usuario': resena_usuario,
        'form': form,
    }
    return render(request, 'detalle_producto.html', contexto)


# CORRECCIÓN: solo admin, solo POST y get_object_or_404
# (en la plantilla el botón debe ser un <form method="post"> con {% csrf_token %})
@login_required
@user_passes_test(admin)
@require_POST
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, "Producto eliminado correctamente.")
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

        # Leemos los checkboxes según el HTML
        destacado = 'destacado' in request.POST
        mas_vendido = 'mas_vendido' in request.POST
        es_nuevo = 'nuevo' in request.POST

        if not (nombre and precio and stock and porciones and categoria_id):
            messages.error(request, "Faltan campos obligatorios.")
            # CORRECCIÓN: mismo nombre de plantilla que el render final
            return render(request, "editar-producto.html", {
                "producto": producto,
                "categorias": categorias,
            })

        producto.nombre = nombre
        producto.descripcion = descripcion or ""
        producto.precio = float(precio)
        producto.stock = int(stock)
        producto.porciones = int(porciones)
        producto.ventas = int(ventas) if ventas else 0
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

    return render(request, "editar-producto.html", {
        "producto": producto,
        "categorias": categorias,
    })


# CORRECCIÓN: protegida con login y admin
@login_required
@user_passes_test(admin)
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
        es_nuevo = request.POST.get('nuevo') == 'on'

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
    return render(request, 'lista_productos.html', {"productos": productos})


@login_required
def armar_pedido_view(request):
    # 1. Buscamos el carrito del usuario actual
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    items_carrito = carrito.items.all()

    # Si el carrito está vacío, rebota al catálogo
    if not items_carrito.exists():
        messages.warning(request, "Debes elegir al menos un producto para armar un pedido.")
        return redirect('catalogo')

    # Calculamos el total
    subtotal = sum(item.subtotal() for item in items_carrito)

    # GUARDAR EL PEDIDO CUANDO SE ENVÍA EL FORMULARIO
    if request.method == 'POST':
        tipo_entrega = request.POST.get('tipo_entrega')
        fecha_str = request.POST.get('fecha')
        hora = request.POST.get('hora')
        direccion_cliente = request.POST.get('direccion', '').strip()
        comentarios_cliente = request.POST.get('comentarios', '').strip()
        telefono_ingresado = request.POST.get('telefono', '').strip()

        # --- Validar el teléfono (solo dígitos, entre 7 y 15) ---
        telefono = re.sub(r'\D', '', telefono_ingresado)
        if not (7 <= len(telefono) <= 15):
            messages.error(request, "Ingresa un número de teléfono válido para contactarte.")
            return redirect('armar_pedido')

        # --- Validar tipo de entrega ---
        # Si tu modelo tiene Pedido.TIPOS_ENTREGA usa: [t[0] for t in Pedido.TIPOS_ENTREGA]
        tipos_validos = ['domicilio', 'recojo']
        if tipo_entrega not in tipos_validos:
            messages.error(request, "Selecciona un tipo de entrega válido.")
            return redirect('armar_pedido')

        # --- Validar fecha y hora obligatorias ---
        fecha_obj = parse_date(fecha_str) if fecha_str else None
        if not fecha_obj or not hora:
            messages.error(request, "Selecciona la fecha y la hora de entrega.")
            return redirect('armar_pedido')

        # --- Validar fecha bloqueada ---
        if FechaBloqueada.objects.filter(fecha=fecha_obj).exists():
            messages.error(
                request,
                f"Lo sentimos, el día {fecha_obj} no está disponible porque la pastelería está cerrada (día libre)."
            )
            return redirect('armar_pedido')

        # --- Ubicación según el tipo de entrega ---
        if tipo_entrega == 'recojo':
            ubicacion_texto = "La Arboleda Campestre, Conjunto Almendros"
        else:
            # En domicilio la dirección es obligatoria (max 250 = Pedido.direccion_entrega)
            if not direccion_cliente:
                messages.error(request, "Ingresa la dirección de entrega para el domicilio.")
                return redirect('armar_pedido')
            ubicacion_texto = direccion_cliente[:250]

        # Nota ordenada en los comentarios del pedido
        # "Fecha de entrega" debe coincidir con _extraer_fecha_pedido
        nota_horario = (
            f"Entrega: {tipo_entrega.upper()} | Dirección: {ubicacion_texto} | "
            f"Fecha de entrega: {fecha_str} | Hora: {hora}"
        )
        if comentarios_cliente:
            nota_horario += f" | Notas: {comentarios_cliente}"

        # Evaluamos los items una sola vez (con su producto)
        items = list(items_carrito.select_related('producto'))

        # --- Validar stock ANTES de crear nada ---
        for item in items:
            if item.cantidad > item.producto.stock:
                messages.error(
                    request,
                    f"No hay suficiente stock de {item.producto.nombre} (quedan {item.producto.stock})."
                )
                return redirect('ver_carrito')

        # Todo en una transacción: o se guarda todo o nada
        with transaction.atomic():
            nuevo_pedido = Pedido.objects.create(
                cliente=request.user,
                nombre_contacto=request.user.username,
                telefono_contacto=telefono,
                direccion_entrega=ubicacion_texto,
                domicilio=tipo_entrega,
                subtotal=subtotal,
                total=subtotal,
                comentarios=nota_horario
            )

            lineas_productos = []
            for item in items:
                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.producto.precio
                )
                # Descuenta stock y suma ventas de forma segura
                Producto.objects.filter(id=item.producto_id).update(
                    stock=F('stock') - item.cantidad,
                    ventas=F('ventas') + item.cantidad
                )
                lineas_productos.append(
                    f"• {item.cantidad} x {item.producto.nombre} (${item.subtotal():,.0f})"
                )

            # Vaciamos el carrito
            items_carrito.delete()

        # Armamos el mensaje y redirigimos a WhatsApp
        mensaje = (
            f"Hola, quiero confirmar mi pedido #{nuevo_pedido.id}\n\n"
            f"Cliente: {request.user.username}\n"
            f"Teléfono: {telefono}\n\n"
            f"Productos:\n" + "\n".join(lineas_productos) + "\n\n"
            f"Subtotal: ${subtotal:,.0f}\n"
            f"Tipo de entrega: {nuevo_pedido.get_domicilio_display()}\n"
            f"Dirección: {ubicacion_texto}\n"
            f"Fecha: {fecha_str}\n"
            f"Hora: {hora}\n"
            f"Notas: {comentarios_cliente or 'Sin notas'}"
        )

        url_whatsapp = f"https://wa.me/{settings.WHATSAPP_NUMERO}?text={quote(mensaje)}"
        return redirect(url_whatsapp)

    # Fechas bloqueadas como lista de strings para el JSON del calendario
    fechas_qs = FechaBloqueada.objects.all().order_by('fecha')
    fechas_bloqueadas_json = [f.fecha.strftime('%Y-%m-%d') for f in fechas_qs]

    contexto = {
        'items': items_carrito,
        'subtotal': subtotal,
        'fechas_bloqueadas': fechas_qs,
        'fechas_bloqueadas_json': fechas_bloqueadas_json,
        # Precarga el teléfono con el del perfil (si lo tiene)
        'telefono_inicial': getattr(getattr(request.user, 'perfil', None), 'telefono', ''),
    }
    return render(request, 'armar_pedido.html', contexto)


@login_required
def ver_carrito_view(request):
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito.items.all()

    # Total acumulado
    total = sum(item.subtotal() for item in items)

    contexto = {
        'items': items,
        'total': total
    }
    return render(request, 'carrito.html', contexto)


@login_required
def eliminar_item_carrito(request, item_id):
    # Eliminar un producto del carrito
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    nombre_producto = item.producto.nombre
    item.delete()

    messages.success(request, f"Eliminaste {nombre_producto} de tu carrito.")
    return redirect('ver_carrito')


@require_POST
@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)

    item, creado = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)

    if not creado:
        item.cantidad += 1
        item.save()

    messages.success(request, f"¡{producto.nombre} agregado al carrito!")
    return redirect('ver_carrito')


# CORRECCIÓN: protegida con login y admin
@login_required
@user_passes_test(admin)
def avanzar_estado_categoria(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if producto.estado == 'DISPONIBLE':
        producto.estado = 'AGOTADO'
        producto.save()
    elif producto.estado == 'AGOTADO':
        producto.estado = 'DISPONIBLE'
        producto.save()

    return redirect('lista_productos')


# CORRECCIÓN: protegida con login y admin
@login_required
@user_passes_test(admin)
def gestionar_fechas_bloqueadas_view(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')

        # 1. Acción de BLOQUEAR
        if accion == 'bloquear':
            fecha_str = request.POST.get('fecha')
            motivo = request.POST.get('motivo', '')

            if fecha_str:
                fecha_obj = parse_date(fecha_str)
                if fecha_obj:
                    obj, created = FechaBloqueada.objects.get_or_create(
                        fecha=fecha_obj,
                        defaults={'motivo': motivo}
                    )
                    if created:
                        messages.success(request, f"El día {fecha_obj} ha sido bloqueado.")
                    else:
                        messages.warning(request, f"El día {fecha_obj} ya estaba bloqueado.")
                else:
                    messages.error(request, "Formato de fecha inválido.")
            return redirect('gestionar_fechas_bloqueadas')

        # 2. Acción de HABILITAR (Desbloquear)
        elif accion == 'habilitar':
            fechas_ids = request.POST.getlist('fechas_seleccionadas')
            if fechas_ids:
                FechaBloqueada.objects.filter(id__in=fechas_ids).delete()
                messages.success(request, "Las fechas seleccionadas han sido habilitadas nuevamente.")
            else:
                messages.warning(request, "No seleccionaste ninguna fecha para habilitar.")
            return redirect('gestionar_fechas_bloqueadas')

    fechas_bloqueadas = FechaBloqueada.objects.all().order_by('fecha')
    return render(request, 'bloquear_fechas.html', {'fechas_bloqueadas': fechas_bloqueadas})


# HU-033: MIS PEDIDOS (CLIENTE)
@login_required
def mis_pedidos_view(request):
    # Solo los pedidos de este cliente, más nuevos primero
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-creado')

    contexto = {
        'pedidos': pedidos
    }
    return render(request, 'mis_pedidos.html', contexto)


@login_required
@user_passes_test(admin)
def lista_pedidos_admin_view(request):
    # La dueña ve todos los pedidos, del más reciente al más antiguo
    pedidos = Pedido.objects.all().order_by('-creado')
    contexto = {
        'pedidos': pedidos,
        'estados': Pedido.ESTADOS,  # estados permitidos para el selector
    }
    return render(request, 'lista_pedidos_admin.html', contexto)


@login_required
@user_passes_test(admin)
def cambiar_estado_pedido_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        estados_validos = [e[0] for e in Pedido.ESTADOS]

        if nuevo_estado in estados_validos:
            pedido.estado = nuevo_estado
            pedido.save()

            # Registramos el cambio en el historial del pedido
            HistorialEstadoPedido.objects.create(
                pedido=pedido,
                estado=nuevo_estado,
                comentario="Estado actualizado por la administración.",
                usuario=request.user
            )

            messages.success(
                request,
                f"¡El estado del pedido #{pedido.id} fue actualizado a '{pedido.get_estado_display()}'!"
            )
        else:
            messages.error(request, "Estado inválido.")

    return redirect('lista_pedidos_admin')


# =========================================================
# HU: PEDIDOS PENDIENTES (DUEÑA)
# =========================================================

@login_required
@user_passes_test(admin)
def pedidos_pendientes_view(request):
    """
    Lista los pedidos en estado 'pendiente' con:
      - fotos de cada producto (producto.imagen o primera de su galería)
      - comentarios del cliente (Pedido.comentarios)
      - detalles (cantidad, precio, subtotal, datos de entrega y totales)
    """
    detalles_qs = (
        DetallePedido.objects
        .select_related('producto')
        .prefetch_related('producto__imagenes')
    )

    pedidos = (
        Pedido.objects
        .filter(estado='pendiente')
        .select_related('cliente', 'cupon', 'direccion')
        .prefetch_related(Prefetch('detalles', queryset=detalles_qs))
        .order_by('creado')  # el más viejo primero
    )

    return render(request, 'pedidos_pendientes.html', {'pedidos': pedidos})


# =========================================================
# HU: ACEPTAR Y ENTREGAR PEDIDOS
# =========================================================

def _extraer_fecha_pedido(comentarios):
    """Extrae la fecha 'YYYY-MM-DD' del texto de comentarios del pedido."""
    if not comentarios:
        return None
    # Busca el patrón "Fecha de entrega: YYYY-MM-DD"
    match = re.search(r"Fecha de entrega:\s*(\d{4}-\d{2}-\d{2})", comentarios)
    if match:
        return parse_date(match.group(1))
    return None


@login_required
@user_passes_test(admin)
@require_POST
def aceptar_pedido_view(request, pedido_id):
    """Cambia el pedido a 'confirmado' y resta un cupo a la fecha elegida."""
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='pendiente')

    # 1. Extraer la fecha y restar el cupo
    fecha_entrega = _extraer_fecha_pedido(pedido.comentarios)

    if fecha_entrega:
        cupo, creado = CupoFecha.objects.get_or_create(
            fecha=fecha_entrega,
            defaults={'cupos_disponibles': ConfiguracionAgenda.obtener().cupo_maximo_por_dia}
        )
        # Restamos 1, evitando que baje de 0
        if cupo.cupos_disponibles > 0:
            cupo.cupos_disponibles -= 1
            cupo.save()
            messages.success(request, f"Pedido #{pedido.id} aceptado. Se restó 1 cupo para el {fecha_entrega}.")
        else:
            messages.warning(request, f"Pedido #{pedido.id} aceptado. Pero NO quedaban cupos para el {fecha_entrega}.")
    else:
        messages.info(request, f"Pedido #{pedido.id} aceptado. (No se encontró fecha para restar cupo).")

    # 2. Cambiar estado
    pedido.estado = 'confirmado'
    pedido.save()

    # 3. Registrar en el historial
    HistorialEstadoPedido.objects.create(
        pedido=pedido,
        estado='confirmado',
        comentario="Pedido aceptado por la administración.",
        usuario=request.user
    )

    return redirect('todos_los_pedidos')


@login_required
@user_passes_test(admin)
@require_POST
def marcar_entregado_view(request, pedido_id):
    """Cambia el estado a 'entregado', lo que hará que desaparezca de la lista activa."""
    pedido = get_object_or_404(Pedido, id=pedido_id)

    pedido.estado = 'entregado'
    pedido.save()

    HistorialEstadoPedido.objects.create(
        pedido=pedido,
        estado='entregado',
        comentario="Pedido marcado como entregado.",
        usuario=request.user
    )

    messages.success(request, f"¡Pedido #{pedido.id} entregado con éxito! Ya no aparecerá en la lista.")
    return redirect('todos_los_pedidos')


@login_required
@user_passes_test(admin)
def todos_los_pedidos_view(request):
    busqueda = request.GET.get("buscar", "").strip()

    pedidos = (
        Pedido.objects
        .filter(estado__in=['confirmado', 'preparacion'])
        .select_related('cliente')
        .prefetch_related('detalles__producto__imagenes')
        .order_by('creado')
    )

    if busqueda:
        pedidos = pedidos.filter(
            Q(nombre_contacto__icontains=busqueda) |
            Q(telefono_contacto__icontains=busqueda) |
            Q(direccion_entrega__icontains=busqueda) |
            Q(creado__date__icontains=busqueda) |
            Q(detalles__producto__nombre__icontains=busqueda)
        ).distinct()

    return render(
        request,
        'todos_los_pedidos.html',
        {'pedidos': pedidos, 'busqueda': busqueda},
    )
