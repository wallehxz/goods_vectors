import json
from django.contrib import admin
from account.models import Consumer, PddUser


@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('mobile', 'username', 'role_name', 'last_login')

    def role_name(self, obj):
        return obj.role_display()

    role_name.short_description = '角色'


@admin.register(PddUser)
class PddUserAdmin(admin.ModelAdmin):
    list_display = ('mobile', 'sms_code', 'created_at', 'updated_at')
