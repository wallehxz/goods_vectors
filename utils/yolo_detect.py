import uuid
from django.conf import settings
from ultralytics import YOLO
import cv2
import os


def image_objects(image_path):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'detects', f'{uuid.uuid4()}')
    os.makedirs(output_dir, exist_ok=True)
    model = YOLO("yolov8m-world.pt")
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
    for i, box in enumerate(results[0].boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cropped_object = image[y1:y2, x1:x2]

        object_filename = f"object_{i + 1}_{results[0].names[int(box.cls)]}.jpg"
        object_path = os.path.join(output_dir, object_filename)
        cv2.imwrite(object_path, cropped_object)
        detection_info['objects_path'][str(uuid.uuid4())] = object_path
        detection_info['detected_objects'].append({
            'object_id': i + 1,
            'class_name': results[0].names[int(box.cls)],
            'class_id': int(box.cls),
            'confidence': float(box.conf),
            'bounding_box': [x1, y1, x2, y2],
            'cropped_image_path': object_path
        })
    detection_info['total_objects'] = len(detection_info['detected_objects'])
    return detection_info
