from django.contrib import admin

# Register your models here.
from .models import Profile, Stuff


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'username', 'first_name',
                    'last_name', 'contact', 'passport', 'birthday')
    list_editable = ('first_name', 'last_name', 'contact', 'passport', 'birthday')


@admin.register(Stuff)
class StuffAdmin(admin.ModelAdmin):
    list_display = ('description', 'profile', 'quantity', 'period', 'price', 'code', 'storage')


