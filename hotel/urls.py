from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, CustomLogoutView


app_name = 'hotel'

urlpatterns = [
    path('', views.index, name='index'),
    path('rooms/', views.room_list, name='room_list'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/new/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/new/', views.customer_create, name='customer_create'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/generate/<int:reservation_id>/', views.invoice_generate, name='invoice_generate'),
    path('invoices/<int:pk>/pay/', views.invoice_mark_paid, name='invoice_mark_paid'),
    path('rooms/new/', views.room_create, name='room_create'),
    path('rooms/<int:pk>/edit/', views.room_edit, name='room_edit'),
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
    path('roomtypes/', views.roomtype_list, name='roomtype_list'),
    path('roomtypes/new/', views.roomtype_create, name='roomtype_create'),
    path('roomtypes/<int:pk>/edit/', views.roomtype_edit, name='roomtype_edit'),
    path('roomtypes/<int:pk>/delete/', views.roomtype_delete, name='roomtype_delete'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    ]