import base64
import json
import uuid
import os
import time
import asyncio
from django.core.files.base import ContentFile
from django.shortcuts import render
from goods.models import Goods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Case, When
from utils.yolo_detect import image_objects


def index(request):
    q = request.GET.get('q', '')
    if os.path.exists(os.path.join(settings.BASE_DIR, 'yolo-best.pt')):
        trained_model = True
        size_bytes = os.path.getsize(os.path.join(settings.BASE_DIR, 'yolo-best.pt'))
        trained_size = int(size_bytes / (1024 * 1024))
    else:
        trained_model = False
    yolo_model = cache.get('yolo_model', 'yolov8x-world.pt')
    image_path = request.GET.get('image_path', '')
    object_path = request.GET.get('object_path', '')
    if q != '':
        goods_list = Goods.objects.filter(name__contains=q).all()
    elif image_path != '' or object_path != '':
        detect_objects = cache.get(request.session.get('image_uuid'))
        goods_list, simi_index = image_query(request)
    else:
        goods_list = Goods.objects.all().order_by('-updated_at')
    paginator = Paginator(goods_list, 91)
    page_number = request.GET.get('page', 1)
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    params = params.urlencode()
    page_obj = paginator.get_page(page_number)
    return render(request, 'index.html', locals())


def image_query(request):
    simi_index = {}
    image_path = request.GET.get('image_path', '')
    object_path = request.GET.get('object_path', '')
    image_vector = cache.get(image_path)
    if image_path != '':
        image_vector = cache.get(image_path)
        if image_vector is None:
            return [], {}
    elif object_path != '':
        image_uuid = request.session.get('image_uuid')
        if image_uuid is None:
            return [], {}
        cache_objects = cache.get(image_uuid)
        if cache_objects is None:
            return [], {}
        obj_image_path = cache_objects.get(object_path)
        image_vector = Goods.image_to_embedding(obj_image_path)
    milvus_results = Goods.similar_vectors(image_vector)
    simi_index = {str(key): int((1 - value) * 100) for key, value in milvus_results}
    goods_ids, similarities = zip(*milvus_results)
    goods_list = Goods.objects.filter(id__in=goods_ids).annotate(
        similarity=Case(
            *[When(id=goods_id, then=similarity) for goods_id, similarity in milvus_results],
            default=0.0
        )
    ).order_by('similarity')
    print(f'search {len(goods_ids)} goods with vector {image_path}')
    return goods_list, simi_index


@csrf_exempt
def image_upload(request):
    uploaded_file = request.FILES.get('file', None)
    image_path = temp_upload(uploaded_file)
    image_vector = Goods.image_to_embedding(image_path)
    path = uuid.uuid4()
    cache.set(f'{path}', image_vector)
    if request.POST.get('yolo', '0') == '1':
        objects_list = image_objects(image_path)
        if objects_list:
            if request.session.get('image_uuid') is None:
                image_uuid = str(uuid.uuid4())
                request.session['image_uuid'] = image_uuid
            else:
                image_uuid = request.session.get('image_uuid')
            print('current image uuid: ', image_uuid)
            cache.set(image_uuid, objects_list['objects_path'])
    else:
        image_uuid = request.session.get('image_uuid')
        if request.session.get('image_uuid'):
            cache.set(image_uuid, [])
    if os.path.exists(image_path):
        print('Delete temp image:', image_path)
        os.remove(image_path)
    return JsonResponse({"status": "success", "path": path}, safe=False)


def set_yolo_model(request):
    model_name = request.GET.get('model', '')
    if model_name != '':
        cache.set('yolo_model', model_name, timeout=None)
        return JsonResponse({"status": "success", "model": model_name}, safe=False)


def temp_upload(uploaded_file):
    temp_dir = os.path.join(settings.MEDIA_ROOT, 'temps')
    os.makedirs(temp_dir, exist_ok=True)  # 确保目录存在
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}.{uploaded_file.name.split('.')[-1]}")
    with open(temp_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
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


def image_to_base64(image_path):
    pre_head = 'data:image/jpeg;base64,'
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return pre_head + encoded_string


@csrf_exempt
def image_to_vector(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        verify_flag = data.get('flag', '')
        if verify_flag != settings.VERIFY_FLAG:
            return JsonResponse({"status": "Unauthorized"}, safe=False)
        file_path = decode_base64_file(data.get('image'))
        image_vector = Goods.image_to_embedding(file_path)
        yolo_object = data.get('yolo', 1)
        objects_list = []
        if yolo_object == 1:
            start_yolo = time.perf_counter()
            objects_path = image_objects(file_path)['objects_path']
            for obj, img_path in objects_path.items():
                obj_img = {'object': os.path.basename(img_path), 'base64_str': image_to_base64(img_path), 'vector': Goods.image_to_embedding(img_path)}
                objects_list.append(obj_img)
            end_yolo = time.perf_counter()
            print(f'yolo detect total time: {end_yolo - start_yolo}')
        return JsonResponse({"status": "success", "vector": image_vector, "objects": objects_list}, safe=False)
    return JsonResponse({"status": "Unauthorized"}, safe=False)


@csrf_exempt
def goods_to_vectors(request):
    time_limit = 55  # 设定时间限制为一分钟
    start_time = time.time()
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        verify_flag = data.get('flag', '')
        if verify_flag != settings.VERIFY_FLAG:
            return JsonResponse({"status": "Unauthorized"}, safe=False)
        goods_list = data.get('goods', [])
        print(f"processing goods total: {len(goods_list)}")
        vectors_list = []
        for good in goods_list:
            image_url = good.get('list_url')
            try:
                image_path = asyncio.run(Goods.temp_image_path(image_url))
                if image_path:
                    image_vector = Goods.image_to_embedding(image_path)
                    vector = {"id": good.get('id'), 'vector': image_vector, 'state': 200}
                    vectors_list.append(vector)
                else:
                    vectors_list.append({"id": good.get('id'), 'state': 404})
            except Exception as e:
                vectors_list.append({"id": good.get('id'), 'state': 500})
                print(f"Error：{e}")
                print(f"image_url: {image_url}")
            if time.time() - start_time >= time_limit:
                break
        print(f"completed vectors total: {len(vectors_list)}")
        return JsonResponse({"status": "success", "vectors": vectors_list}, safe=False)
    return JsonResponse({"status": "Unauthorized"}, safe=False)

# Create your views here.
