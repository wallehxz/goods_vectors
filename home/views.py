import base64
import json
import uuid
import os
import time
import asyncio
import math
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
from utils.pdd_api import search_keywords, goods_detail, jpk_goods_search, cats_list
from utils.browser import AsyncBrowser
from utils.playwright_manager import get_browser, pdd_user_login, close_browser, parse_nested_json, get_available_mobile
from account.models import PddUser


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



def pdd_index(request):
    params = request.GET.copy()
    if params.get('keyword'):
        params['page_size'] = 70
        result  = search_keywords(params)
        goods_list = result.get('goods_list')
        if goods_list:
            params['list_id'] = result.get('list_id')
            total_count = result.get('total_count')
            total_page = total_page = math.ceil(total_count / 70)
            current_page = int(params.get('page', 1))
            prev_page = current_page - 1
            next_page = current_page + 1
            range_page = range(1, total_page + 1)
        else:
            return JsonResponse(result, safe=False)
    if params.get('page'):
        del params['page']
    params = params.urlencode()
    return render(request, 'pdd_index.html', locals())


def pdd_show(request):
    goods_sign = request.GET.get('goods_sign')
    result = goods_detail(goods_sign).get("goods_details")[0]
    discount = int((result.get("min_normal_price") - result.get("min_group_price")) / result.get("min_normal_price") * 100)
    return render(request, 'pdd_show.html', locals())

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

@csrf_exempt
def pdd_goods_search(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        verify_flag = data.get('flag', '')
        if verify_flag != settings.VERIFY_FLAG:
            return JsonResponse({"status": "Unauthorized"}, safe=False)
        result =  search_keywords(data)
        # result =  jpk_goods_search(keyword, page, list_id)
        return JsonResponse({"status": "success", "result": result}, safe=False)

@csrf_exempt
def pdd_goods_detail(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        verify_flag = data.get('flag', '')
        if verify_flag != settings.VERIFY_FLAG:
            return JsonResponse({"status": "Unauthorized"}, safe=False)
        goods_sign = data.get('goods_sign', '')
        result =  goods_detail(goods_sign)
        return JsonResponse({"status": "success", "result": result}, safe=False)

@csrf_exempt
def pdd_cats_list(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        verify_flag = data.get('flag', '')
        if verify_flag != settings.VERIFY_FLAG:
            return JsonResponse({"status": "Unauthorized"}, safe=False)
        result = cats_list()
        return JsonResponse({"status": "success", "result": result}, safe=False)


async def web_pdd_search(request):
    manager = AsyncBrowser()
    try:
        context = await manager.get_browser()
        page = await manager.get_page()
        keyword = request.GET.get('keyword', '')
        await manager.pdd_user_login(context, page)
        await page.goto("https://mobile.yangkeduo.com")
        await page.click('div._2fnObgNt._215Ua8G9')
        await page.locator('input[type=search]').fill(keyword)
        await page.click('div.RuSDrtii')
        print(f'current page: {page.url}')
        await manager.smooth_scroll(page)
        content = await page.content()
        return JsonResponse({"status": "success", "page": content}, safe=False)
    except Exception as e:
        return JsonResponse({"status": "error", "msg": str(e)}, safe=False)
    finally:
        await page.close()
        await context.close()

async def web_pdd_detail(request):
    # try:
        goods_id = request.GET.get('goods_id')
        show_url = f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}"
        browser = await get_browser()
        mobile = await get_available_mobile()
        pdd_login_state = cache.get(f"pdd_{mobile}_cookies", None)
        if pdd_login_state:
            context = await browser.new_context(
                storage_state=pdd_login_state,
                viewport = {"width": 390, "height": 844},  # 逻辑像素
                device_scale_factor = 3,  # 设备像素比（DPR）
                user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                is_mobile = True,
                has_touch = True
            )
            page = await context.new_page()
        else:
            context = await browser.new_context(
                viewport={"width": 390, "height": 844},  # 逻辑像素
                device_scale_factor=3,  # 设备像素比（DPR）
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                is_mobile=True,
                has_touch=True
            )
            page = await context.new_page()
            await pdd_user_login(page, mobile)
        await page.goto(show_url)
        if 'login.html' in page.url:
            cache.set('pdd_login_state', None)
            print(f"cache login state invalid")
            await pdd_user_login(page, mobile)
            await page.goto(show_url)
        # content = await page.content()
        raw_data = await page.evaluate("() => window.rawData")
        goods = raw_data["store"]["initDataObj"]["goods"]
        await close_browser()
        return JsonResponse({"status": "success", "current": mobile,"goods": parse_nested_json(goods)}, safe=False)
    # except Exception as e:
    #     await close_browser()
    #     return JsonResponse({"status": "error", "msg": str(e)}, safe=False)

# Create your views here.
