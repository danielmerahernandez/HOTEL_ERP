from django import forms
from .models import Reservation, Customer, Room, RoomType  # ← Importa Room

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['customer', 'room', 'check_in', 'check_out']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ahora 'Room' está definido porque lo importamos
        self.fields['room'].queryset = Room.objects.filter(is_available=True)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'document_id', 'address']

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'is_available']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 101'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'room_number': 'Número de habitación',
            'room_type': 'Tipo de habitación',
            'is_available': '¿Disponible?',
        }

class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'description', 'price_per_night']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }