from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import user_passes_test, permission_required, login_required
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth import views as auth_views

def register(request):
    datos = ''
    errores = []
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        datos = request.POST

        #validacion:
        if password1 != password2:
            errores.append('la constraseñas no coinciden')
        if User.objects.filter(username=username).exists():
            errores.append('el usuario ya existe')
        if User.objects.filter(email=email).exists():
            errores.append('el correo ya esta registrado')

        if not errores:
            user = User.objects.create_user(
                username = username,
                email = email,
                password = password1,
                first_name = first_name,
                last_name = last_name,
            )
            login(request,user)
            return redirect('home')

    return render(request, 'register.html',{'errore': errores, 'datos' : datos})


@login_required
def editar_perfil(request):
    errores = []
    usuario = request.user  

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

    
        if User.objects.filter(username=username).exclude(pk=usuario.pk).exists():
            errores.append('El nombre de usuario ya está en uso por otra cuenta.')


        if User.objects.filter(email=email).exclude(pk=usuario.pk).exists():
            errores.append('El correo electrónico ya está registrado en otra cuenta.')


        if not errores:
            usuario.username = username
            usuario.email = email
            usuario.first_name = first_name
            usuario.last_name = last_name
            usuario.save()

            messages.success(request, 'Tus datos personales han sido actualizados con éxito.')
            return redirect('editar_perfil')

    return render(request, 'editar_perfil.html', {
        'errores': errores,
        'usuario': usuario
    })

@login_required
def cambiar_contrasena(request):
    errores = []
    usuario = request.user

    if request.method == 'POST':
        password_actual = request.POST.get('password_actual')
        password_nuevo = request.POST.get('password_nuevo')
        password_confirmar = request.POST.get('password_confirmar')


        if not usuario.check_password(password_actual):
            errores.append('La contraseña actual es incorrecta.')

        if password_nuevo != password_confirmar:
            errores.append('Las nuevas contraseñas no coinciden.')

        if len(password_nuevo) < 8:
            errores.append('La nueva contraseña debe tener al menos 6 caracteres.')

        if not errores:
            usuario.set_password(password_nuevo)  # Encripta y cambia la contraseña
            usuario.save()
            
            # Nota importante: Cambiar la contraseña cierra la sesión en Django por seguridad.
            # Para evitar que se desconecte de inmediato, actualizamos la sesión:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, usuario)

            messages.success(request, 'Tu contraseña ha sido actualizada con éxito.')
            return redirect('cambiar_contrasena')

    return render(request, 'cambiar_contrasena.html', {
        'errores': errores
    })


class PasswordResetView(auth_views.PasswordResetView):
    """Paso 1: el usuario escribe su correo y se le envía el enlace."""
    template_name = 'password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Si el correo está registrado, te enviamos un enlace para restablecer la contraseña.'
        )
        return response


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Paso 2: página que dice 'revisa tu correo'."""
    template_name = 'password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Paso 3: el usuario define la nueva contraseña. Django valida el token."""
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Tu contraseña ha sido restablecida con éxito.')
        return response


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Paso 4: página final de éxito."""
    template_name = 'password_reset_complete.html'