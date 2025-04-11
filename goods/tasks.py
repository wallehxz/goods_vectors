import time
from datetime import datetime
from celery import shared_task
import json
import sys
import os
from django.conf import settings
from utils.redis_client import get_redis_client
from django.core.serializers import serialize
from django.core.serializers import deserialize
import multiprocessing
from goods.models import Goods


def process_worker():
    cache = get_redis_client().client()
    while True:
        try:
            serialized_obj = cache.lpop('un_vector_list')
            if serialized_obj:
                json_data = json.dumps([json.loads(serialized_obj)])
                deserialized_objects = deserialize('json', json_data)
                for obj in deserialized_objects:
                    goods = obj.object
                    goods.update_vector()
                    print(f"{multiprocessing.current_process().name} processing goods id: {goods.id}")
            else:
                break
        except Exception as e:
            print(e)


@shared_task
def image_to_vector():
    from goods.models import Goods
    cache = get_redis_client().client()
    print(f'Current un vector goods :{cache.llen("un_vector_list")}')
    if cache.llen('un_vector_list') == 0:
        queryset = Goods.objects.all()
        serialized_objects = serialize('json', queryset)
        objects = json.loads(serialized_objects)
        with cache.pipeline() as pipe:
            for obj in objects:
                pipe.rpush('un_vector_list', json.dumps(obj))
            pipe.execute()
        print(f'Goods size: {cache.llen("un_vector_list")}')

    processes = []
    for i in range(2):
        process = multiprocessing.Process(target=process_worker)
        process.start()
        processes.append(process)

    for process in processes:
        process.join()


@shared_task
def check_train(task_id):
    from cates.models import YoloTask
    task = YoloTask.objects.get(id=task_id)
    if task.status == 2:
        if sys.platform == 'win32':
            # runs/detect/train/weights/best.pt
            train_path = os.path.join(settings.BASE_DIR, 'runs/detect/train')
        else:
            # yolo_train/datasets/runs/detect/train/weights/best.pt
            train_path = os.path.join(settings.BASE_DIR, 'yolo_train/datasets/runs/detect/train')
        if not os.path.exists(train_path):
            print(f"train path not build，Wait 15 seconds")
            time.sleep(15)
        timeout_seconds = 10 * 60
        last_file_count = len(os.listdir(train_path))
        last_activity_time = time.time()
        try:
            while True:
                current_file_count = len(os.listdir(train_path))
                # 如果文件数量增加，重置计时器
                train_complete = False
                if current_file_count > last_file_count:
                    print(f"new file! count: {current_file_count}")
                    last_file_count = current_file_count
                    last_activity_time = time.time()
                # 检查是否超时
                elapsed_time = time.time() - last_activity_time
                if elapsed_time >= timeout_seconds:
                    print(f"10 minute no new file build")
                    break
                for root, _, files in os.walk(train_path):
                    if 'best.pt' in files:
                        print('best.pt generate Training complete')
                        train_complete = True
                        break
                if train_complete:
                    break
                time.sleep(30)
        except Exception as e:
            print(f"Error: {e}")
        if len(os.listdir(train_path)) > 2:
            task.status = 3
            task.save()
        else:
            task.status = 4
            task.save()
        return True


@shared_task
def download_image():
    cache = get_redis_client().client()
    if cache.llen('download_products') > 0:
        print(f'Prepare to download {cache.llen("download_products")} image')
        date_str = datetime.now().strftime("%Y%m%d")
        base_dir = f'products/{date_str}'
        store_dir = os.path.join(settings.MEDIA_ROOT, base_dir)
        os.makedirs(store_dir, exist_ok=True)
        while True:
            img_url = cache.lpop('download_products')
            if img_url:
                next_num = len(os.listdir(store_dir)) + 1
                format_jpg = "{:08d}.jpg".format(next_num)
                Goods.temp_image_path(img_url, format_jpg, base_dir)
            else:
                break



