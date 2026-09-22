from django import forms
from .models import Producto


INPUT_CLASS = "w-full rounded-2xl border border-chocolate/20 bg-crema px-4 py-3 text-sm font-medium text-chocolate outline-none transition focus:border-chocolate/60 focus:bg-white"


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'precio', 'imagen',
            'porciones', 'stock', 'disponible',
            'destacado', 'mas_vendido', 'es_nuevo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ej: Torta de Chocolate'}),
            'descripcion': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Descripción del producto...'}),
            'precio': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '1000', 'min': '0', 'placeholder': '45000'}),
            'porciones': forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '8'}),
            'stock': forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': '10'}),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-chocolate/70 file:mr-4 file:rounded-full file:border-0 file:bg-chocolate file:px-5 file:py-2 file:text-sm file:font-bold file:text-crema hover:file:bg-chocolate/90 cursor-pointer'
            }),
            'disponible': forms.CheckboxInput(attrs={'class': 'h-4 w-4 accent-chocolate'}),
            'destacado': forms.CheckboxInput(attrs={'class': 'h-4 w-4 accent-chocolate'}),
            'mas_vendido': forms.CheckboxInput(attrs={'class': 'h-4 w-4 accent-chocolate'}),
            'es_nuevo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 accent-chocolate'}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0.')
        return precio

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock

    def clean_porciones(self):
        porciones = self.cleaned_data.get('porciones')
        if porciones is not None and porciones < 1:
            raise forms.ValidationError('Debe haber al menos 1 porción.')
        return porciones