import json
from django.contrib import admin
from django.http import JsonResponse
from django.utils.html import format_html
from simpleui.admin import AjaxAdmin
from goods.models import Goods

admin.site.site_header = '商品管理后台'
admin.site.site_title = '商品管理后台'
admin.site.index_title = '商品管理后台'


@admin.register(Goods)
class GoodsAdmin(AjaxAdmin):
    list_display = ('name', 'price', 'preview', 'is_vector', 'has_embedding', 'created_at')
    search_fields = ['name']
    list_per_page = 25
    actions = ['export_data', ]

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete_vector()
        super().delete_queryset(request, queryset)

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
            return obj.get_vector_shape()
        else:
            return '--'

    has_embedding.short_description = '向量规模'

    def export_data(self, request, queryset):
        json_file = request.FILES['upload']
        data = json.load(json_file)
        region_list = []
        for item in data:
            region_list.append(Goods(
                name=item.get('title'),
                price=item.get('api_price'),
                image_url=item.get('list_url')
            ))
        Goods.objects.bulk_create(region_list)
        return JsonResponse(data={
            'status': 'success',
            'msg': '处理成功！'
        })

    export_data.short_description = '商品数据'
    export_data.type = 'success'
    export_data.icon = 'el-icon-upload'
    export_data.enable = True

    export_data.layer = {
        'title': '批量导入商品',
        'tips': '导入商品后会异步转换向量数据',
        'params': [{
            'type': 'file',
            'key': 'upload',
            'label': '文件'
        }]
    }
# Register your models here.
