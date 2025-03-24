from django.contrib import admin
from django.utils.html import format_html
from goods.models import Goods

admin.site.site_header = '商品管理后台'
admin.site.site_title = '商品管理后台'
admin.site.index_title = '商品管理后台'


@admin.register(Goods)
class GoodsAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'preview', 'has_embedding', 'created_at')
    search_fields = ['name']
    list_per_page = 25

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="75" height="75">', obj.image.url)
        elif obj.image_url:
            return format_html('<img src="{}" width="75" height="75">', obj.image_url)
        else:
            return '--'

    preview.short_description = '商品预览'

    def has_embedding(self, obj):
        if obj.check_by_embedding():
            return '已转换'
        else:
            return '未转换'

    has_embedding.short_description = '图片向量'

# Register your models here.
