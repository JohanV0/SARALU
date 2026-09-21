from django.shortcuts import render , redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request,'home.html')