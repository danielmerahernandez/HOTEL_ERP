from .forms import RoomForm 
import datetime # al inicio
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Room, Reservation, Customer, Invoice
from .forms import ReservationForm, CustomerForm
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth, ExtractWeekDay
#from datetime import datetime, timedelta
from django.contrib.auth.views import LoginView, LogoutView
import calendar

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    template_name = 'registration/logged_out.html'


@login_required
def index(request):
    total_rooms = Room.objects.count()
    today = timezone.now().date()

    occupied_rooms = Reservation.objects.filter(
        status__in=['confirmed', 'checked_in'],
        check_in__lte=today,
        check_out__gt=today
    ).values('room').distinct().count()

    available_rooms = total_rooms - occupied_rooms
    today_reservations = Reservation.objects.filter(check_in=today).count()
    recent_reservations = Reservation.objects.order_by('-created_at')[:5]

    # Datos para gráficos
    # 1. Días de semana
    weekday_counts = [0] * 7
    reservations_week = Reservation.objects.filter(
        status__in=['confirmed', 'checked_in', 'checked_out']
    )
    for r in reservations_week:
        weekday_counts[r.check_in.weekday()] += 1
    weekday_data = weekday_counts[6:7] + weekday_counts[0:6]  # domingo a sábado

    # 2. Meses del año actual (automático)
    current_year = today.year
    month_labels = []
    month_data = []
    for month in range(1, 13):
        # Usamos datetime.date (del módulo importado)
        month_date = datetime.date(current_year, month, 1)
        month_labels.append(month_date.strftime('%b %Y'))
        # Calcular último día del mes
        if month == 12:
            end_date = datetime.date(current_year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(current_year, month + 1, 1) - datetime.timedelta(days=1)
        count = Reservation.objects.filter(
            check_in__gte=month_date,
            check_in__lte=end_date,
            status__in=['confirmed', 'checked_in', 'checked_out']
        ).count()
        month_data.append(count)

    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'today_reservations': today_reservations,
        'recent_reservations': recent_reservations,
        'weekday_data': weekday_data,
        'month_labels': month_labels,
        'month_data': month_data,
    }
    return render(request, 'hotel/index.html', context)

@login_required
def room_list(request):
    rooms = Room.objects.all()
    available_filter = request.GET.get('available')
    if available_filter == '1':
        rooms = rooms.filter(is_available=True)
    context = {'rooms': rooms}
    return render(request, 'hotel/room_list.html', context)

@login_required
def reservation_list(request):
    reservations = Reservation.objects.select_related('customer', 'room').all()
    status = request.GET.get('status')
    if status:
        reservations = reservations.filter(status=status)
    context = {'reservations': reservations}
    return render(request, 'hotel/reservation_list.html', context)

@login_required
def reservation_create(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()
            messages.success(request, 'Reserva creada exitosamente.')
            return redirect('hotel:reservation_detail', pk=reservation.pk)
    else:
        form = ReservationForm()
    return render(request, 'hotel/reservation_form.html', {'form': form, 'title': 'Nueva Reserva'})

@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'check_in':
            reservation.status = 'checked_in'
            reservation.save()
            messages.success(request, 'Check-in realizado.')
            return redirect('hotel:reservation_detail', pk=reservation.pk)
        elif action == 'check_out':
            reservation.status = 'checked_out'
            reservation.save()
            messages.success(request, 'Check-out realizado.')
            return redirect('hotel:reservation_detail', pk=reservation.pk)
        elif action == 'cancel':
            reservation.status = 'cancelled'
            reservation.save()
            messages.success(request, 'Reserva cancelada.')
            return redirect('hotel:reservation_detail', pk=reservation.pk)
    return render(request, 'hotel/reservation_detail.html', {'reservation': reservation})

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    context = {'customers': customers}
    return render(request, 'hotel/customer_list.html', context)

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado exitosamente.')
            return redirect('hotel:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'hotel/customer_form.html', {'form': form, 'title': 'Nuevo Cliente'})

# Vistas de facturación
@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('reservation__customer', 'reservation__room').all()
    status = request.GET.get('status')
    if status:
        invoices = invoices.filter(status=status)
    context = {'invoices': invoices}
    return render(request, 'hotel/invoice_list.html', context)

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'hotel/invoice_detail.html', {'invoice': invoice})

@login_required
def invoice_generate(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    if hasattr(reservation, 'invoice'):
        messages.warning(request, 'Esta reserva ya tiene una factura asociada.')
        return redirect('hotel:invoice_detail', pk=reservation.invoice.pk)
    invoice = Invoice.objects.create(
        reservation=reservation,
        total_amount=reservation.total_price
    )
    messages.success(request, f'Factura {invoice.invoice_number} generada correctamente.')
    return redirect('hotel:invoice_detail', pk=invoice.pk)

@login_required
def invoice_mark_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status != 'paid':
        invoice.status = 'paid'
        invoice.save()
        messages.success(request, 'Factura marcada como pagada.')
    else:
        messages.info(request, 'La factura ya estaba pagada.')
    return redirect('hotel:invoice_detail', pk=invoice.pk)

@login_required
def room_create(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habitación creada correctamente.')
            return redirect('hotel:room_list')
    else:
        form = RoomForm()
    return render(request, 'hotel/room_form.html', {'form': form, 'title': 'Nueva Habitación'})

@login_required
def room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habitación actualizada.')
            return redirect('hotel:room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'hotel/room_form.html', {'form': form, 'title': 'Editar Habitación'})

@login_required
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Habitación eliminada.')
        return redirect('hotel:room_list')
    return render(request, 'hotel/room_confirm_delete.html', {'room': room})

from .models import RoomType
from .forms import RoomTypeForm

@login_required
def roomtype_list(request):
    roomtypes = RoomType.objects.all()
    return render(request, 'hotel/roomtype_list.html', {'roomtypes': roomtypes})

@login_required
def roomtype_create(request):
    if request.method == 'POST':
        form = RoomTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de habitación creado.')
            return redirect('hotel:roomtype_list')
    else:
        form = RoomTypeForm()
    return render(request, 'hotel/roomtype_form.html', {'form': form, 'title': 'Nuevo Tipo de Habitación'})

@login_required
def roomtype_edit(request, pk):
    roomtype = get_object_or_404(RoomType, pk=pk)
    if request.method == 'POST':
        form = RoomTypeForm(request.POST, instance=roomtype)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de habitación actualizado.')
            return redirect('hotel:roomtype_list')
    else:
        form = RoomTypeForm(instance=roomtype)
    return render(request, 'hotel/roomtype_form.html', {'form': form, 'title': 'Editar Tipo de Habitación'})

@login_required
def roomtype_delete(request, pk):
    roomtype = get_object_or_404(RoomType, pk=pk)
    if request.method == 'POST':
        roomtype.delete()
        messages.success(request, 'Tipo de habitación eliminado.')
        return redirect('hotel:roomtype_list')
    return render(request, 'hotel/roomtype_confirm_delete.html', {'roomtype': roomtype})
