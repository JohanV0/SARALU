from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.urls import reverse

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