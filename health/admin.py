from django.contrib import admin
from .models import User, ConsultationSlot, UserManager
# Register your models here.

admin.site.register(User)
admin.site.register(ConsultationSlot)
# admin.site.register(UserManager)