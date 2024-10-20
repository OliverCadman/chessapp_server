from django.contrib import admin
from core.models import User, Room, Player

# Register your models here.
admin.site.register(User)
admin.site.register(Room)
admin.site.register(Player)