import json
from django.contrib import admin
from django.contrib import messages
from django.http import JsonResponse
from django.utils.html import format_html
from simpleui.admin import AjaxAdmin
from utils.redis_client import get_redis_client
from goods.models import Goods, Product
from goods.tasks import download_image

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


@admin.register(Product)
class ProductAdmin(AjaxAdmin):
    list_display = ('title', 'preview')
    search_fields = ['title']
    change_list_template = 'admin/goods/product/change_list.html'
    actions = ['download_selected']

    def get_list_display_links(self, request, list_display):
        return None

    def get_queryset(self, request):
        return super().get_queryset(request).using('mysql_db')

    def preview(self, obj):
        if obj.list_url:
            return format_html('<img src="{}" width="75" height="75">', obj.list_url)
        else:
            return '--'

    preview.short_description = '预览'

    def download_selected(self, request, queryset):
        cache = get_redis_client().client()
        with cache.pipeline() as pipe:
            for obj in queryset:
                pipe.rpush('download_products', obj.list_url)
            pipe.execute()
        messages.success(request, f'{len(queryset)} 张商品图片已加入下载队列 <br> 当前图片总数：{cache.llen("download_products")}')
        cache.expire('download_products', 60 * 60 * 24)
        download_image.delay()

    download_selected.short_description = '下载图片'
    download_selected.icon = 'el-icon-download'

# Register your models here.
