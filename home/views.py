import base64
import json
import uuid
import os

from django.core.files.base import ContentFile
from django.shortcuts import render
from goods.models import Goods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Case, When


def index(request):
    q = request.GET.get('q', '')
    path = request.GET.get('image_path', '')
    if q != '':
        goods_list = Goods.objects.filter(name__contains=q).all()
    elif path != '':
        image_vector = cache.get(path)
        milvus_results = Goods.similar_vectors(image_vector)
        goods_ids, similarities = zip(*milvus_results)
        goods_list = Goods.objects.filter(id__in=goods_ids).annotate(
            similarity=Case(
                *[When(id=goods_id, then=similarity) for goods_id, similarity in milvus_results],
                default=0.0
            )
        ).order_by('similarity')
    else:
        goods_list = Goods.objects.all().order_by('-updated_at')
        paginator = Paginator(goods_list, 91)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    return render(request, 'index.html', locals())


@csrf_exempt
def image_upload(request):
    uploaded_file = request.FILES.get('file', None)
    image_path = temp_upload(uploaded_file)
    image_vector = Goods.get_resnet_vector(image_path)
    # image_vector = Goods.image_to_vector(image_path)
    if os.path.exists(image_path):
        print('删除临时文件:', image_path)
        os.remove(image_path)
    path = uuid.uuid4()
    cache.set(f'{path}', image_vector)
    return JsonResponse({"status": "success", "path": path}, safe=False)


def temp_upload(uploaded_file):
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
    os.makedirs(temp_dir, exist_ok=True)  # 确保目录存在
    temp_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_path, 'wb') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return temp_path


def decode_base64_file(data):
    if isinstance(data, str) and data.startswith('data:'):
        header, data = data.split(';base64,')
        file_ext = header.split('/')[-1]
        decoded_file = base64.b64decode(data)
        file_name = f"{uuid.uuid4()}.{file_ext}"
        save_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, file_name)
        with open(file_path, 'wb') as destination:
            for chunk in ContentFile(decoded_file).chunks():
                destination.write(chunk)
        return file_path
    raise ValueError("无效的 base64 文件数据")


@csrf_exempt
def image_to_vector(request):
    if request.method == 'POST':
        base64_data = json.loads(request.body.decode('utf-8'))['image']
        file_path = decode_base64_file(base64_data)
        image_vector = Goods.get_resnet_vector(file_path)
        return JsonResponse({"status": "success", "vector": image_vector}, safe=False)
    return JsonResponse({"status": "error"}, safe=False)


@csrf_exempt
def goods_to_vectors(request):
    if request.method == 'POST':
        goods_list = json.loads(request.body.decode('utf-8'))['goods']
        vectors_list = []
        for good in goods_list:
            image_url = good.get('list_url')
            image_path = Goods.temp_image_path(image_url)
            image_vector = Goods.get_resnet_vector(image_path)
            vector = {"id": good.get('id'), 'vector': image_vector}
            vectors_list.append(vector)
        return JsonResponse({"status": "success", "vectors": vectors_list}, safe=False)
    return JsonResponse({"status": "error"}, safe=False)

# Create your views here.
