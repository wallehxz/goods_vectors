import os
import sys
import shutil
import zipfile
import subprocess

import yaml
from django.contrib import admin
from django.http import FileResponse
from django.shortcuts import redirect
from cates.models import Category, YoloTask
from django.urls import reverse
from django.utils.html import format_html
from django.conf import settings
from django.contrib import messages
from goods.tasks import check_train
from django.core.cache import cache


def data_train(task):
    try:
        dataset_dir = os.path.join(settings.BASE_DIR, 'yolo_train', 'datasets')
        conda_env = "goods_vectors"
        default_model = os.path.join(settings.BASE_DIR, 'yolov8x-world.pt')
        if task.trained_model and task.trained_model.path:
            trained_model = task.trained_model.path
        else:
            trained_model = default_model
        if sys.platform == "win32":
            command = f'yolo train model={trained_model} data=dataset.yaml epochs={task.epochs} imgsz=640 batch=8 pretrained=True workers=0'
            print("Training on Windows")
            windows_cmd = f'start cmd /c "conda activate {conda_env} && {command}"'
            subprocess.run(windows_cmd, shell=True, check=True, cwd=dataset_dir)
            check_train.delay(task.id)
        else:
            print("Training on Linux")
            command = f'yolo train model={trained_model} data=dataset.yaml epochs={task.epochs} imgsz=640 batch=8 pretrained=True'
            screen_name = f"yolo_train_dataset"
            screen_cmd = f"screen -dmS {screen_name} bash -c 'cd {dataset_dir} && {command}'"
            subprocess.run(screen_cmd, shell=True, check=True)
            check_train.delay(task.id)
        task.status = 2
        task.save()
    except Exception as e:
        print(f"Error: {e}")
        task.status = 4
        task.save()


def build_train(request, pk):
    task = YoloTask.objects.get(pk=pk)
    if task.status == 1:
        zip_path = task.data_zip.path
        datasets_dir = os.path.join(settings.BASE_DIR, 'yolo_train', 'datasets')
        extract_dir = os.path.join(datasets_dir, 'original')
        if os.path.exists(datasets_dir):
            shutil.rmtree(datasets_dir)
        os.makedirs(datasets_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        sub_dirs = ['train', 'val']
        ori_images_dir = os.path.join(extract_dir, 'images')
        ori_labels_dir = os.path.join(extract_dir, 'labels')
        for sub in sub_dirs:
            images_dir = os.path.join(datasets_dir, 'images', sub)
            os.makedirs(images_dir, exist_ok=True)
            copy_all_files(ori_images_dir, images_dir)
            labels_dir = os.path.join(datasets_dir, 'labels', sub)
            os.makedirs(labels_dir, exist_ok=True)
            copy_all_files(ori_labels_dir, labels_dir)
        dataset = {"path": "../", "train": "images/train", "val": "images/val"}
        if sys.platform == "win32":
            dataset['path'] = '../goods_vectors/yolo_train/datasets/'
            runs_path = os.path.join(settings.BASE_DIR, 'runs')
            if os.path.exists(runs_path):
                shutil.rmtree(runs_path)
        names = {}
        with open(os.path.join(extract_dir, 'classes.txt'), 'r') as f:
            for number, line in enumerate(f):
                names[number] = line.strip()
        dataset['names'] = names
        dataset_yaml = os.path.join(datasets_dir, 'dataset.yaml')
        with open(dataset_yaml, "w", encoding="utf-8") as f:
            yaml.dump(dataset, f, default_flow_style=False, sort_keys=False)
        shutil.copyfile(os.path.join(settings.BASE_DIR, 'yolo11n.pt'), os.path.join(datasets_dir, 'yolo11n.pt'))
        data_train(task)
    messages.success(request, f"开始训练模型中，请耐心等待...")
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


def copy_all_files(src_folder, dst_folder):
    for item in os.listdir(src_folder):
        src_path = os.path.join(src_folder, item)
        dst_path = os.path.join(dst_folder, item)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)


def down_model(request, pk):
    if sys.platform == "win32":
        trained_path = os.path.join(settings.BASE_DIR, 'runs/detect/train/weights/best.pt')
    else:
        trained_path = os.path.join(settings.BASE_DIR, 'yolo_train/datasets/runs/detect/train/weights/best.pt')
    if os.path.exists(trained_path):
        response = FileResponse(open(trained_path, 'rb'))
        response['Content-Disposition'] = 'attachment; filename="yolo_new_world.pt"'
        return response
    else:
        messages.error(request, f"新模型训练中，暂未完成，请耐心等待")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))


def apply_model(request):
    if sys.platform == "win32":
        trained_path = os.path.join(settings.BASE_DIR, 'runs/detect/train/weights/best.pt')
    else:
        trained_path = os.path.join(settings.BASE_DIR, 'yolo_train/datasets/runs/detect/train/weights/best.pt')
    if os.path.exists(trained_path):
        new_world_file = os.path.join(settings.BASE_DIR, 'yolo-new-world.pt')
        shutil.copyfile(trained_path, new_world_file)
        cache.set('yolo_model', 'yolo-new-world.pt', timeout=0)
    messages.success(request, f"新模型应用成功")
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'en_name', 'updated_at')
    search_fields = ('name', 'en_name')
    list_per_page = 30


@admin.register(YoloTask)
class YoloTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'data_zip', 'trained_model', 'status', 'epochs', 'updated_at', 'custom_actions')

    def custom_actions(self, obj):
        if obj.status == 1:
            return format_html(
                '<a class="el-button el-button--warning el-button--mini" href="{}" style="color: white !important;padding: 4px 5px;"><i class="el-icon-cpu"></i> 构建训练</a> ',
                reverse('build_train', args=[obj.pk])
            )
        elif obj.status == 3:
            down_link = format_html('<a class="el-button el-button--success el-button--mini" href="{}" style="color: white !important;padding: 4px 5px;"><i class="el-icon-download"></i> 下载</a> ',reverse('down_model', args=[obj.pk]))
            apply_link = format_html('<a class="el-button el-button--danger el-button--mini" href="{}" style="color: white !important;padding: 4px 5px;"><i class="el-icon-hand"></i> 应用</a> ', reverse('apply_model'))
            return format_html('{} {}', down_link, apply_link)

    custom_actions.short_description = '操作'  # 列标题
# Register your models here.
