from celery import shared_task
import json
from utils.redis_client import get_redis_client
from django.core.serializers import serialize
from django.core.serializers import deserialize
import multiprocessing


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
                    print(f"Process {multiprocessing.current_process().name} processing goods id: {goods.id}")
                    goods.update_vector()
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
        queryset = Goods.objects.filter(is_vector=False).all()
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
