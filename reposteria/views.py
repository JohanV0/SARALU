import json
from datetime import date, timedelta
from django.shortcuts import render
from .models import ConfiguracionAgenda, FechaBloqueada, CupoFecha


def home(request):
    """Home con productos destacados, más vendidos y nuevos."""
    return render(request, 'home.html', {
        'destacados': Producto.objects.filter(destacado=True, estado_producto=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True, estado_producto=True),
        'nuevos': Producto.objects.filter(es_nuevo=True, estado_producto=True),
    })


def catalogo(request):
    """Catálogo público de productos."""
    productos = Producto.objects.filter(estado_producto=True).order_by('-fecha_creacion')
    return render(request, 'catalogo.html', {'productos': productos})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto
from .forms import ProductoForm


def home(request):
    """Home con productos destacados, más vendidos y nuevos."""
    return render(request, 'home.html', {
        'destacados': Producto.objects.filter(destacado=True, estado_producto=True),
        'mas_vendidos': Producto.objects.filter(mas_vendido=True, estado_producto=True),
        'nuevos': Producto.objects.filter(es_nuevo=True, estado_producto=True),
    })


def catalogo(request):
    """Catálogo público de productos."""
    productos = Producto.objects.filter(estado_producto=True).order_by('-fecha_creacion')
    return render(request, 'catalogo.html', {'productos': productos})


def detalle_producto(request, producto_id):
    """Detalle del producto con sugerencias relacionadas (sin categoría)."""
    producto = get_object_or_404(Producto, id=producto_id)

    # 1. Productos más vendidos (excluyendo el actual)
    relacionados = list(
        Producto.objects.filter(
            mas_vendido=True,
            estado_producto=True
        ).exclude(id=producto.id)[:4]
    )

    # 2. Si no hay más vendidos, mostrar cualquier otro producto disponible
    if not relacionados:
        relacionados = list(
            Producto.objects.filter(
                estado_producto=True
            ).exclude(id=producto.id)[:4]
        )

    return render(request, 'detalle_producto.html', {
        'producto': producto,
        'relacionados': relacionados,
    })


def registrar_producto(request):
    """Registrar producto."""
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'¡{producto.nombre} registrado correctamente!')
            return redirect('lista_productos')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm()

    return render(request, 'registrar_producto.html', {'form': form})


def lista_productos(request):
    """Lista de todos los productos."""
    productos = Producto.objects.all().order_by('-fecha_creacion')
    return render(request, 'lista_productos.html', {'productos': productos})


def editar_producto(request, producto_id):
    """Modificar producto existente."""
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡{producto.nombre} actualizado correctamente!')
            return redirect('lista_productos')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'editar_producto.html', {
        'form': form,
        'producto': producto,
    })

def registrar_producto(request):
    """Registrar producto."""
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'¡{producto.nombre} registrado correctamente!')
            return redirect('lista_productos')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm()

    return render(request, 'registrar_producto.html', {'form': form})


def lista_productos(request):
    """Lista de todos los productos."""
    productos = Producto.objects.all().order_by('-fecha_creacion')
    return render(request, 'lista_productos.html', {'productos': productos})


def editar_producto(request, producto_id):
    """Modificar producto existente."""
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'¡{producto.nombre} actualizado correctamente!')
            return redirect('lista_productos')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'editar_producto.html', {
        'form': form,
        'producto': producto,
    })
def calendario_cliente(request):
    '''
    Construye el calendario de los próximos 60 días usando los
    modelos ConfiguracionAgenda, FechaBloqueada y CupoFecha.
    Envía un JSON al template con el estado de cada fecha.
    '''
    hoy = date.today()
    fin = hoy + timedelta(days=60)

    # Configuración global (cupo máximo por defecto)
    config = ConfiguracionAgenda.obtener()
    cupo_maximo = config.cupo_maximo_por_dia

    # Fechas bloqueadas en el rango (1 sola consulta)
    bloqueadas = set(
        FechaBloqueada.objects
        .filter(fecha__gte=hoy, fecha__lte=fin)
        .values_list('fecha', flat=True)
    )

    # Cupos personalizados por fecha (1 sola consulta)
    cupos_por_fecha = {
        c.fecha: c.cupos_disponibles
        for c in CupoFecha.objects.filter(fecha__gte=hoy, fecha__lte=fin)
    }

    # Recorremos día por día y armamos la lista final
    fechas = []
    for i in range((fin - hoy).days + 1):
        dia = hoy + timedelta(days=i)

        # a) Si está bloqueada, no hay nada más que revisar
        if dia in bloqueadas:
            fechas.append({
                'fecha': dia.isoformat(),
                'cupos': 0,
                'total': 0,
                'estado': 'bloqueado',
            })
            continue

        # b) Total de cupos para ese día (personalizado o global)
        total = cupos_por_fecha.get(dia, cupo_maximo)

        # c) Reservados: cuando actives Pedido, se calcula aquí
        reservados = 0

        cupos = max(0, total - reservados)
        estado = 'lleno' if cupos <= 0 else 'disponible'

        fechas.append({
            'fecha': dia.isoformat(),
            'cupos': cupos,
            'total': total,
            'estado': estado,
        })

    return render(request, 'calendario.html', {
        'fechas_json': json.dumps(fechas),
    })