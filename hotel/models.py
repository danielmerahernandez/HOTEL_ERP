from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class RoomType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tipo de habitación")
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio por noche")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tipo de habitación"
        verbose_name_plural = "Tipos de habitación"

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True, verbose_name="Número de habitación")
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    is_available = models.BooleanField(default=True, verbose_name="¿Disponible?")

    def __str__(self):
        return f"{self.room_number} - {self.room_type.name}"

    class Meta:
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"

class Customer(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Nombres")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    document_id = models.CharField(max_length=20, unique=True, verbose_name="Documento de identidad")
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.document_id}"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmada'),
        ('checked_in', 'Hospedado'),
        ('checked_out', 'Finalizada'),
        ('cancelled', 'Cancelada'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reservations')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reservations')
    check_in = models.DateField(verbose_name="Fecha de ingreso")
    check_out = models.DateField(verbose_name="Fecha de salida")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError("La fecha de salida debe ser posterior a la fecha de ingreso.")
        if self.room_id:
            overlapping = Reservation.objects.filter(
                room=self.room,
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
                status__in=['confirmed', 'checked_in']
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError("La habitación ya está reservada en esas fechas.")

    def save(self, *args, **kwargs):
        if not self.total_price:
            nights = (self.check_out - self.check_in).days
            if nights > 0 and self.room and self.room.room_type:
                self.total_price = self.room.room_type.price_per_night * nights
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva de {self.customer} - Hab. {self.room.room_number}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagada'),
    ]

    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    issue_date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.invoice_number} - {self.reservation.customer}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            today = timezone.now().strftime('%Y%m%d')
            last_invoice = Invoice.objects.filter(invoice_number__startswith=f'INV-{today}').order_by('invoice_number').last()
            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.invoice_number = f'INV-{today}-{new_num:04d}'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"