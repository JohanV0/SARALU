# reposteria/forms.py
from django import forms
from .models import Resena

class ResenaForm(forms.ModelForm):
    class Meta:
        model = Resena
        fields = ['calificacion', 'comentario']
        labels = {
            'calificacion': 'Calificación (1 a 5 estrellas)',
            'comentario': 'Tu opinión',
        }
        widgets = {
            'comentario': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'w-full rounded-xl border border-chocolate/20 p-3 outline-none focus:border-chocolate focus:ring-1 focus:ring-chocolate transition',
                'placeholder': '¿Qué te pareció este producto?'
            }),
            'calificacion': forms.NumberInput(attrs={
                'min': 1, 'max': 5, 
                'class': 'w-20 rounded-xl border border-chocolate/20 p-2 outline-none focus:border-chocolate transition'
            })
        }