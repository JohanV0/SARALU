import re
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
from .forms import ResenaForm
from .models import (
    Carrito,Categoria,ConfiguracionAgenda,CupoFecha,
    DetallePedido,FechaBloqueada,HistorialEstadoPedido,
    ItemCarrito,Pedido,Producto,Resena,RespuestaResena,
    HorarioAtencion,
)

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
        'productos_relacionados': productos_relacionados,
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
        estado = request.POST.get("estado")  # 'DISPONIBLE' o 'AGOTADO'

        # Leemos los checkboxes correctamente según el HTML
        destacado = 'destacado' in request.POST
        mas_vendido = 'mas_vendido' in request.POST
        es_nuevo = 'nuevo' in request.POST

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

    paginator = Paginator(productos, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    extra_query = query_params.urlencode()

    contexto ={
            "productos":productos,
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

        # 1. Validar teléfono (formulario o perfil del usuario)
        telefono_perfil = ""
        if hasattr(request.user, 'perfil') and request.user.perfil.telefono:
            telefono_perfil = request.user.perfil.telefono.strip()
        telefono_final = telefono_form or telefono_perfil

        if not telefono_final:
            messages.error(request, "Debes ingresar un teléfono de contacto para coordinar tu pedido.")
            return redirect('armar_pedido')

        # 2. Validar tipo de entrega y dirección
        if tipo_entrega not in ['domicilio', 'recojo']:
            messages.error(request, "Tipo de entrega no válido.")
            return redirect('armar_pedido')

        if tipo_entrega == 'domicilio':
            if not direccion_cliente:
                messages.error(request, "Debes ingresar una dirección de entrega para pedidos a domicilio.")
                return redirect('armar_pedido')
            ubicacion_texto = direccion_cliente
        else:
            ubicacion_texto = "La Arboleda Campestre, Conjunto Almendros, Ibagué"

        # 3. Validar fecha (no vacía, válida, no pasada, no bloqueada)
        if not fecha_str:
            messages.error(request, "Debes seleccionar una fecha de entrega.")
            return redirect('armar_pedido')

        fecha_obj = parse_date(fecha_str)
        if not fecha_obj:
            messages.error(request, "El formato de la fecha no es válido.")
            return redirect('armar_pedido')

        hoy = timezone.localdate()
        if fecha_obj < hoy:
            messages.error(request, "No puedes elegir una fecha pasada.")
            return redirect('armar_pedido')

        if FechaBloqueada.objects.filter(fecha=fecha_obj).exists():
            messages.error(request, f"Lo sentimos, el día {fecha_obj} no está disponible porque la pastelería está cerrada.")
            return redirect('armar_pedido')

        # 4. Validar hora (no vacía, válida y dentro del horario de atención del día)
        if not hora_str:
            messages.error(request, "Debes seleccionar una hora aproximada.")
            return redirect('armar_pedido')

        try:
            hora_obj = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "El formato de la hora no es válido.")
            return redirect('armar_pedido')

        # En Python weekday(): Lunes=0 ... Domingo=6 (coincide con HorarioAtencion.DIAS)
        dia_semana = fecha_obj.weekday()
        horario_dia = HorarioAtencion.objects.filter(dia=dia_semana).first()
        if horario_dia:
            if not horario_dia.activo:
                messages.error(request, f"La pastelería no atiende los {horario_dia.get_dia_display().lower()}s.")
                return redirect('armar_pedido')
            if not (horario_dia.hora_apertura <= hora_obj <= horario_dia.hora_cierre):
                messages.error(
                    request,
                    f"La hora debe estar entre {horario_dia.hora_apertura.strftime('%H:%M')} y {horario_dia.hora_cierre.strftime('%H:%M')}."
                )
                return redirect('armar_pedido')

        nota_horario = f"Entrega: {tipo_entrega.upper()} | Dirección: {ubicacion_texto} | Fecha: {fecha_str} | Hora: {hora_str}"
        if comentarios_cliente:
            nota_horario += f" | Notas: {comentarios_cliente}"

        # 5. Guardar todo de forma atómica (o se guarda todo o nada)
        try:
            with transaction.atomic():
                nuevo_pedido = Pedido.objects.create(
                    cliente=request.user,
                    nombre_contacto=request.user.get_full_name() or request.user.username,
                    telefono_contacto=telefono_final,
                    direccion_entrega=ubicacion_texto,
                    domicilio=tipo_entrega,
                    subtotal=subtotal,
                    total=subtotal,
                    comentarios=nota_horario
                )

                for item in items_carrito:
                    DetallePedido.objects.create(
                        pedido=nuevo_pedido,
                        producto=item.producto,
                        cantidad=item.cantidad,
                        precio_unitario=item.producto.precio
                    )

                items_carrito.delete()
        except Exception:
            messages.error(request, "Ocurrió un problema al registrar tu pedido. Intenta nuevamente.")
            return redirect('armar_pedido')

        messages.success(request, f"¡Tu pedido #{nuevo_pedido.id} ha sido confirmado con éxito!")
        return redirect('home')

    fechas_qs = FechaBloqueada.objects.all().order_by('fecha')
    fechas_bloqueadas_json = [f.fecha.strftime('%Y-%m-%d') for f in fechas_qs]

    contexto = {
        'items': items_carrito,
        'subtotal': subtotal,
        'fechas_bloqueadas': fechas_qs,
        'fechas_bloqueadas_json': fechas_bloqueadas_json,
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
    return render(request, 'carrito.html', contexto)

@login_required
def eliminar_item_carrito(request, item_id):
    # CRITERIO 4: Eliminar un producto del carrito
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

def avanzar_estado_categoria(request, producto_id):
    categorias = get_object_or_404(Producto, id=producto_id)

    if categorias.estado == 'DISPONIBLE':
        categorias.estado = 'AGOTADO'
        categorias.save()
    elif categorias.estado == 'AGOTADO':
        categorias.estado = 'DISPONIBLE'
        categorias.save()

    return redirect('lista_productos')

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
    busqueda = request.GET.get("buscar", "").strip()
    estado = request.GET.get("estado", "").strip()

    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-creado')

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

    paginator = Paginator(pedidos, 8) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    contexto = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Pedido.ESTADOS, # Enviamos los estados para el <select> del HTML
    }
    
    return render(request, 'mis_pedidos.html', contexto)

@login_required
@user_passes_test(admin)
def lista_pedidos_admin_view(request):  
    # La dueña puede ver todos los pedidos ordenados del más reciente al más antiguo
    pedidos = Pedido.objects.all().order_by('-creado')
    contexto = {
        'pedidos': pedidos,
        'estados': Pedido.ESTADOS, # Pasamos los estados permitidos para el selector
    }
    return render(request, 'lista_pedidos_admin.html', contexto)

@login_required
@user_passes_test(admin)
def cambiar_estado_pedido_view(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        estados_validos = [e[0] for e in Pedido.ESTADOS]

        if nuevo_estado not in estados_validos:
            messages.error(request, "Estado inválido.")
            return redirect('lista_pedidos_admin')

        estado_anterior = pedido.estado

        # Regla: no marcar como entregado un pedido pendiente o cancelado
        if nuevo_estado == 'entregado' and estado_anterior in ['pendiente', 'cancelado']:
            messages.error(
                request,
                f"No puedes marcar como Entregado el pedido #{pedido.id} porque está '{pedido.get_estado_display()}'."
            )
            return redirect('lista_pedidos_admin')

        try:
            with transaction.atomic():
                pedido.estado = nuevo_estado
                pedido.save()

                if nuevo_estado == 'cancelado' and estado_anterior != 'cancelado':
                    match_fecha = re.search(r'Fecha:\s*([\d\-]+)', pedido.comentarios or '')
                    if match_fecha:
                        fecha_obj = parse_date(match_fecha.group(1))
                        if fecha_obj:
                            FechaBloqueada.objects.filter(fecha=fecha_obj).delete()

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
        except Exception:
            messages.error(request, "No se pudo actualizar el estado del pedido. Intenta de nuevo.")

    return redirect('lista_pedidos_admin')

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
        .order_by('creado')  # el más viejo primero
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

    paginator = Paginator(pedidos, 8) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    contexto = {
        'page_obj': page_obj,
        'busqueda': busqueda,
        'estado': estado,
        'estados': Pedido.ESTADOS, # Enviamos los estados para el <select> del HTML
    }

    return render(request, 'pedidos_pendientes.html', contexto)


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

    return redirect('todos_los_pedidos')

@login_required
@user_passes_test(admin)
@require_POST
def marcar_entregado_view(request, pedido_id):
    """Cambia el estado a 'entregado', lo que hará que desaparezca de la lista activa."""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    pedido.estado = 'entregado'
    pedido.save()
    
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
            Q(nombre_contacto__icontains = busqueda) |
            Q(telefono_contacto__icontains = busqueda) |
            Q(direccion_entrega__icontains = busqueda) |
            Q(creado__date__icontains = busqueda) |
            Q(detalles__producto__nombre__icontains = busqueda)
        ).distinct()

    return render(
        request,
        'todos_los_pedidos.html',
        {'pedidos': pedidos, 'busqueda': busqueda},
    )