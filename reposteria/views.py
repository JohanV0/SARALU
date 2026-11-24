import re
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch, Q ,F , Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
from urllib.parse import quote 
from django.conf import settings  
from .forms import ResenaForm
from .models import (
    Carrito,Categoria,ConfiguracionAgenda,CupoFecha,
    DetallePedido,FechaBloqueada,HistorialEstadoPedido,
    ItemCarrito,Pedido,Producto,Resena,RespuestaResena,
    HorarioAtencion,
)
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
    categoria_code = request.GET.get('categoria')        # "TARTAS", "CUPCAKES", ...
    productos = Producto.objects.select_related('categoria').prefetch_related('imagenes').order_by("nombre")
    categorias = Categoria.objects.all()
    if categoria_code:
        productos = productos.filter(categoria__categoria=categoria_code)
    paginator = Paginator(productos, 2) #para saber la cantidad de itenas van a aparecer
    page_number = request.GET.get("page") #para saber el numero de la pagina desde la URL
    page_obj = paginator.get_page(page_number) #get_page evita error si se elije numero fuera del que hay (inicio o final)
    query_params = request.GET.copy()
    query_params.pop('page', None)
    extra_query = query_params.urlencode()
    contexto = {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': categoria_code,
        'page_obj' : page_obj,          
        'extra_query' : extra_query,
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
        .filter(categoria=producto.categoria)
        .exclude(id=producto.id)
        .order_by('-id')[:4]
    )
    resenas = producto.resenas.all().order_by('-fecha_creacion')
    resena_usuario = None
    form = None
    if request.user.is_authenticated:
        resena_usuario = resenas.filter(usuario=request.user).first()
        if request.method == 'POST':
            accion = request.POST.get('accion')
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
            if accion == 'eliminar' and resena_usuario:
                resena_usuario.delete()
                messages.success(request, 'Tu reseña ha sido eliminada.')
                return redirect('producto_detalle', producto_id=producto.id)
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
@login_required
@user_passes_test(admin)
@require_POST
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, "Producto eliminado correctamente.")
    return redirect('lista_productos')
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
        estado = request.POST.get("estado")
        destacado = 'destacado' in request.POST
        mas_vendido = 'mas_vendido' in request.POST
        es_nuevo = 'nuevo' in request.POST
        if not (nombre and precio and stock and porciones and categoria_id):
            messages.error(request, "Faltan campos obligatorios.")
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
        if request.FILES.get('imagen'):
            producto.imagen = request.FILES['imagen']
        producto.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("producto_detalle", producto_id=producto.id)
    return render(request, "editar-producto.html", {
        "producto": producto,
        "categorias": categorias,
    })
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
    busqueda = request.GET.get("buscar", "").strip()
    estado = request.GET.get("estado","").strip()
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains = busqueda) 
        ).distinct()
    if estado:
        productos = productos.filter(estado=estado)
    estados = Producto._meta.get_field('estado').choices 
    paginator = Paginator(productos, 4)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    query_params.pop('page', None)
    extra_query = query_params.urlencode()
    contexto ={
            "productos":page_obj,
            "busqueda" : busqueda,
            "estado" : estado,
            "estados" : estados,
            "page_obj" : page_obj,
            "extra_query" : extra_query,
        }
    return render(request,'lista_productos.html',contexto)
@login_required
def armar_pedido_view(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    items_carrito = carrito.items.select_related('producto').all()
    if not items_carrito.exists():
        messages.warning(request, "Debes elegir al menos un producto para armar un pedido.")
        return redirect('catalogo')
    subtotal = sum(item.subtotal() for item in items_carrito)
    if request.method == 'POST':
        tipo_entrega = request.POST.get('tipo_entrega', 'domicilio').strip()
        fecha_str = request.POST.get('fecha', '').strip()
        hora_str = request.POST.get('hora', '').strip()
        direccion_cliente = request.POST.get('direccion', '').strip()
        telefono_form = request.POST.get('telefono', '').strip()
        comentarios_cliente = request.POST.get('comentarios', '').strip()
        telefono_ingresado = request.POST.get('telefono', '').strip()
        telefono = re.sub(r'\D', '', telefono_ingresado)
        if not (7 <= len(telefono) <= 15):
            messages.error(request, "Ingresa un número de teléfono válido para contactarte.")
            return redirect('armar_pedido')
        tipos_validos = ['domicilio', 'recojo']
        if tipo_entrega not in tipos_validos:
            messages.error(request, "Selecciona un tipo de entrega válido.")
            return redirect('armar_pedido')
        fecha_obj = parse_date(fecha_str) if fecha_str else None
        if not fecha_obj or not hora:
            messages.error(request, "Selecciona la fecha y la hora de entrega.")
            return redirect('armar_pedido')
        if FechaBloqueada.objects.filter(fecha=fecha_obj).exists():
            messages.error(
                request,
                f"Lo sentimos, el día {fecha_obj} no está disponible porque la pastelería está cerrada (día libre)."
            )
            return redirect('armar_pedido')
        if tipo_entrega == 'recojo':
            ubicacion_texto = "La Arboleda Campestre, Conjunto Almendros"
        else:
            if not direccion_cliente:
                messages.error(request, "Ingresa la dirección de entrega para el domicilio.")
                return redirect('armar_pedido')
            ubicacion_texto = direccion_cliente[:250]
        nota_horario = (
            f"Entrega: {tipo_entrega.upper()} | Dirección: {ubicacion_texto} | "
            f"Fecha de entrega: {fecha_str} | Hora: {hora}"
        )
        if comentarios_cliente:
            nota_horario += f" | Notas: {comentarios_cliente}"
        items = list(items_carrito.select_related('producto'))
        for item in items:
            if item.cantidad > item.producto.stock:
                messages.error(
                    request,
                    f"No hay suficiente stock de {item.producto.nombre} (quedan {item.producto.stock})."
                )
                return redirect('ver_carrito')
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
                Producto.objects.filter(id=item.producto_id).update(
                    stock=F('stock') - item.cantidad,
                    ventas=F('ventas') + item.cantidad
                )
                lineas_productos.append(
                    f"• {item.cantidad} x {item.producto.nombre} (${item.subtotal():,.0f})"
                )
            items_carrito.delete()
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
    fechas_qs = FechaBloqueada.objects.all().order_by('fecha')
    fechas_bloqueadas_json = [f.fecha.strftime('%Y-%m-%d') for f in fechas_qs]
    contexto = {
        'items': items_carrito,
        'subtotal': subtotal,
        'fechas_bloqueadas': fechas_qs,
        'fechas_bloqueadas_json': fechas_bloqueadas_json,
        'telefono_inicial': getattr(getattr(request.user, 'perfil', None), 'telefono', ''),
    }
    return render(request, 'armar_pedido.html', contexto)
@login_required
def ver_carrito_view(request):
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito.items.all()
    total = sum(item.subtotal() for item in items)
    contexto = {
        'items': items,
        'total': total
    }
    return render(request, 'carrito.html', contexto)
@login_required
def eliminar_item_carrito(request, item_id):
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
@login_required
@user_passes_test(admin)
def gestionar_fechas_bloqueadas_view(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
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
# =========================================================
# HU: MIS PEDIDOS (CLIENTE)
# - Muestra el estado actual de cada pedido (se actualiza cuando la
#   dueña lo cambia desde el panel, porque ambos leen Pedido.estado)
# - Adjunta el historial de cambios de estado (con su comentario)
# =========================================================
def _datos_entrega_pedido(pedido):
    """
    Lee los datos que el cliente registró al hacer el pedido.
    Se guardan en `pedido.comentarios` con este formato (ver armar_pedido_view):
    "Entrega: X | Dirección: Y | Fecha de entrega: YYYY-MM-DD | Hora: HH:MM | Notas: Z"
    """
    texto = pedido.comentarios or ''
    m_hora = re.search(r"Hora:\s*([^|]+)", texto)
    m_dir = re.search(r"Dirección:\s*([^|]+)", texto)
    m_notas = re.search(r"Notas:\s*(.+)$", texto, re.S)
    return {
        'fecha': _extraer_fecha_pedido(texto),
        'hora': m_hora.group(1).strip() if m_hora else '',
        'direccion': (m_dir.group(1).strip() if m_dir else '') or (pedido.direccion_entrega or ''),
        'notas': m_notas.group(1).strip() if m_notas else '',
    }

@login_required
def mis_pedidos_view(request):
    busqueda = request.GET.get("buscar", "").strip()
    estado = request.GET.get("estado", "").strip()

    pedidos = (
        Pedido.objects
        .filter(cliente=request.user)
        .prefetch_related('detalles__producto')
        .order_by('-creado')
    )

    if busqueda:
        pedidos = pedidos.filter(
            Q(nombre_contacto__icontains=busqueda) |
            Q(telefono_contacto__icontains=busqueda) |
            Q(direccion_entrega__icontains=busqueda) |
            Q(creado__date__icontains=busqueda) |
            Q(detalles__producto__nombre__icontains=busqueda)
        ).distinct()

    if estado:
        pedidos = pedidos.filter(estado=estado)

    paginator = Paginator(pedidos, 2)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Enriquecer SOLO los pedidos de esta página (más eficiente)
    ids_pagina = [p.id for p in page_obj]

    historiales = (
        HistorialEstadoPedido.objects
        .filter(pedido_id__in=ids_pagina)
        .order_by('-id')
    )
    por_pedido = {}
    for h in historiales:
        por_pedido.setdefault(h.pedido_id, []).append(h)

    for pedido in page_obj:
        pedido.historial_lista = por_pedido.get(pedido.id, [])
        datos = _datos_entrega_pedido(pedido)
        pedido.entrega_fecha = datos['fecha']
        pedido.entrega_hora = datos['hora']
        pedido.entrega_direccion = datos['direccion']
        pedido.entrega_notas = datos['notas']

    return render(request, 'mis_pedidos.html', {
        'pedidos' :page_obj,
        'page_obj': page_obj,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Pedido.ESTADOS,
    })


@login_required
@user_passes_test(admin)
def lista_pedidos_admin_view(request):  
    # La dueña puede ver todos los pedidos ordenados del más reciente al más antiguo
    pedidos = Pedido.objects.all().order_by('-creado')
    contexto = {
        'pedidos': pedidos,
        'estados': Pedido.ESTADOS,
    }
    return render(request, 'lista_pedidos_admin.html', contexto)
# =========================================================
# HU: CAMBIAR ESTADO DE UN PEDIDO (DUEÑA)
# =========================================================
@login_required
@user_passes_test(admin)
@require_POST
def cambiar_estado_pedido_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    nuevo_estado = request.POST.get('estado', '').strip()
    comentario = request.POST.get('comentario', '').strip()
    estados_validos = [e[0] for e in Pedido.ESTADOS]
    if nuevo_estado not in estados_validos:
        messages.error(request, "Estado inválido.")
        return redirect('todos_los_pedidos')
    if pedido.estado == nuevo_estado:
        messages.info(
            request,
            f"El pedido #{pedido.id} ya está en '{pedido.get_estado_display()}'."
        )
        return redirect('todos_los_pedidos')
    estado_anterior = pedido.estado
    with transaction.atomic():
        pedido.estado = nuevo_estado
        pedido.save()
        HistorialEstadoPedido.objects.create(
            pedido=pedido,
            estado=nuevo_estado,
            comentario=comentario or (
                f"Cambio de '{dict(Pedido.ESTADOS)[estado_anterior]}' "
                f"a '{pedido.get_estado_display()}' por la administración."
            ),
            usuario=request.user,
        )
    messages.success(
        request,
        f"Pedido #{pedido.id} actualizado a '{pedido.get_estado_display()}'."
    )
    return redirect('todos_los_pedidos')


# =========================================================
# HU: PEDIDOS PENDIENTES (DUEÑA)
# =========================================================
@login_required
@user_passes_test(admin)
def pedidos_pendientes_view(request):
    busqueda = request.GET.get("buscar", "").strip()
    estado = request.GET.get("estado", "").strip()
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
        .order_by('creado')
    )
    if busqueda:
        pedidos = pedidos.filter(
            Q(nombre_contacto__icontains = busqueda) |
            Q(telefono_contacto__icontains = busqueda) |
            Q(direccion_entrega__icontains = busqueda) |
            Q(creado__date__icontains = busqueda) |
            Q(detalles__producto__nombre__icontains = busqueda)
        ).distinct()
    if estado:
        pedidos = pedidos.filter(estado=estado)
    paginator = Paginator(pedidos, 4) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    contexto = {
        'pedidos': page_obj,         
        'page_obj': page_obj,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Pedido.ESTADOS,
    }
    return render(request, 'pedidos_pendientes.html', contexto)
def _extraer_fecha_pedido(comentarios):
    """Extrae la fecha 'YYYY-MM-DD' del texto de comentarios del pedido."""
    if not comentarios:
        return None
    match = re.search(r"Fecha de entrega:\s*(\d{4}-\d{2}-\d{2})", comentarios)
    if match:
        return parse_date(match.group(1))
    return None
@login_required
@user_passes_test(admin)
@require_POST
def aceptar_pedido_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='pendiente')
    pedido.estado = 'confirmado'
    pedido.save()
    HistorialEstadoPedido.objects.create(
        pedido=pedido,
        estado='confirmado',
        comentario="Pedido aceptado por la administración.",
        usuario=request.user
    )
    messages.success(request, f"Pedido #{pedido.id} aceptado.")
    return redirect('todos_los_pedidos')
@login_required
@user_passes_test(admin)
@require_POST
def marcar_entregado_view(request, pedido_id):
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
# =========================================================
# HU: TODOS LOS PEDIDOS (PANEL PRINCIPAL DE LA DUEÑA)
# - Por defecto muestra: confirmado + preparación + entregado + rechazado + cancelado
# - Chips de filtro: confirmado, preparacion, entregado, rechazado, cancelado
#   (pendiente vive en pedidos_pendientes_view)
# =========================================================
@login_required
@user_passes_test(admin)
def todos_los_pedidos_view(request):
    busqueda = request.GET.get("buscar", "").strip()
    estado_filtro = request.GET.get("estado", "").strip()
    estados_validos = [e[0] for e in Pedido.ESTADOS]

    base_qs = (
        Pedido.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto__imagenes')
        .order_by('-creado')
    )

    if estado_filtro in estados_validos and estado_filtro != 'pendiente':
        pedidos = base_qs.filter(estado=estado_filtro)
    else:
        pedidos = base_qs.filter(
            estado__in=['confirmado', 'preparacion', 'entregado', 'rechazado', 'cancelado']
        )
        estado_filtro = ''

    if busqueda:
        pedidos = pedidos.filter(
            Q(nombre_contacto__icontains=busqueda) |
            Q(telefono_contacto__icontains=busqueda) |
            Q(direccion_entrega__icontains=busqueda) |
            Q(detalles__producto__nombre__icontains=busqueda)
        ).distinct()

    # Paginación
    paginator = Paginator(pedidos, 4)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Conteos (sobre el queryset SIN paginar)
    conteos = {estado: 0 for estado, _ in Pedido.ESTADOS}
    for estado, total in (
        Pedido.objects
        .values_list('estado')
        .annotate(total=Count('id'))
        .values_list('estado', 'total')
    ):
        conteos[estado] = total

    return render(
        request,
        'todos_los_pedidos.html',
        {
            'pedidos': page_obj,          # ⚠️ antes: pedidos (queryset completo)
            'page_obj': page_obj,
            'busqueda': busqueda,
            'estados': Pedido.ESTADOS,
            'estado_actual': estado_filtro,
            'conteos': conteos,
        },
    )