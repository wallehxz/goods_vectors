from django.contrib import admin
from cates.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'en_name', 'updated_at')
    search_fields = ('name', 'en_name')
    list_per_page = 30

# Register your models here.
