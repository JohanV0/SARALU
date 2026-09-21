from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.urls import reverse

def register(request):
    pass