import os
import cv2
import uuid
from ultralytics import YOLO

from django.conf import settings
from cates.models import Category
from django.core.cache import cache
from PIL import Image
import imagehash
from collections import defaultdict


def image_objects(image_path):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'detects', f'{uuid.uuid4()}')
    os.makedirs(output_dir, exist_ok=True)
    yolo_model = cache.get('yolo_model', 'yolov8x-world.pt')
    model = YOLO(yolo_model)
    if 'world' in yolo_model:
        cache_list = cache.get('cate_list')
        if cache_list is None:
            model_list = list(model.names.values())
            cate_list = Category.get_categories()
            cache_list = list(set(model_list + cate_list))
            cache.set('cate_list', cache_list, timeout=None)
        model.set_classes(cache_list)
    results = model(image_path)
    if len(results[0].boxes) == 0:
        model = YOLO('yolov8x-oiv7.pt')
        results = model(image_path)
    image = cv2.imread(image_path)
    detection_info = {
        'original_image': image_path,
        'total_objects': 0,
        'detected_objects': [],
        'annotated_image': None
    }
    annotated_image = results[0].plot()
    detection_info['annotated_image'] = os.path.join(output_dir, 'annotated_' + os.path.basename(image_path))
    cv2.imwrite(detection_info['annotated_image'], annotated_image)

    detection_info['objects_path'] = {}
    detection_info['objects_hash'] = {}
    for i, box in enumerate(results[0].boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cropped_object = image[y1:y2, x1:x2]

        object_filename = f"object_{i + 1}_{results[0].names[int(box.cls)]}.jpg"
        object_path = os.path.join(output_dir, object_filename)
        cv2.imwrite(object_path, cropped_object)
        uuid_str = str(uuid.uuid4())
        detection_info['objects_path'][uuid_str] = object_path
        img = Image.open(object_path)
        hash_value = imagehash.phash(img)
        detection_info['objects_hash'][uuid_str] = hash_value
        detection_info['detected_objects'].append({
            'object_id': i + 1,
            'class_name': results[0].names[int(box.cls)],
            'class_id': int(box.cls),
            'confidence': float(box.conf),
            'bounding_box': [x1, y1, x2, y2],
            'cropped_image_path': object_path,
        })
    detection_info['total_objects'] = len(detection_info['detected_objects'])
    duplicates = find_duplicates(detection_info['objects_hash'])
    for item in remove_duplicates(duplicates):
        del detection_info['objects_path'][item]
    print(f'{yolo_model} names total {len(results[0].names.values())}: ', results[0].names.values())
    return detection_info


def find_duplicates(hash_dict, threshold=10):
    """根据哈希值分组相似图片"""
    duplicates = defaultdict(list)
    processed = set()
    for path1, hash1 in hash_dict.items():
        if path1 not in processed:
            group = [path1]
            for path2, hash2 in hash_dict.items():
                if path1 != path2 and path2 not in processed:
                    if hash1 - hash2 <= threshold:  # 汉明距离小于阈值
                        group.append(path2)
                        processed.add(path2)
            if len(group) > 1:
                duplicates[path1] = group
            processed.add(path1)
    return duplicates


def remove_duplicates(duplicates, keep_first=True):
    """删除重复图片（默认保留每组的第一张）"""
    remove_list = []
    for group in duplicates.values():
        for duplicate in (group[1:] if keep_first else group[:-1]):
            remove_list.append(duplicate)
            print(f"已删除重复文件: {duplicate}")
    return remove_list
