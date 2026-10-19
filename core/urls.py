from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Recuperación de contraseña
    path('cuentas/', include('django.contrib.auth.urls')),

    # Rutas de SARALU
    path('', include('accounts.urls')),
    path('', include('reposteria.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
