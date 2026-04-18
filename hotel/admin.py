from django.contrib import admin
from .models import RoomType, Room, Customer, Reservation, Invoice

admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Customer)
admin.site.register(Reservation)
admin.site.register(Invoice)
# Register your models here.
