from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name = 'login.html'), name = 'login'),
    path('logout/', auth_views.LogoutView.as_view(), name = 'logout'),
    path('register/', views.register, name = 'register'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('password-reset/',views.PasswordResetView.as_view(),name='password_reset'),
    path('password-reset/done/',views.PasswordResetDoneView.as_view(),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',views.PasswordResetConfirmView.as_view(),name='password_reset_confirm'),
    path('password-reset-complete/',views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),
]