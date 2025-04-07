import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path
from django.contrib import admin
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect
from cates.models import Category, YoloTask
from django.urls import reverse
from django.utils.html import format_html
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import action


def data_train(request, pk):
    task = YoloTask.objects.get(pk=pk)
    if task.status == 1:
        try:
            zip_path = task.data_zip.path
            extract_dir = os.path.join(settings.BASE_DIR, 'yolo_train')
            os.makedirs(extract_dir, exist_ok=True)
            dataset_dir = os.path.join(extract_dir, 'datasets')
            if os.path.exists(dataset_dir):
                shutil.rmtree(dataset_dir)
            runs_dir = os.path.join(settings.BASE_DIR, 'runs')
            if os.path.exists(runs_dir):
                shutil.rmtree(runs_dir)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            required_dirs = ['images', 'labels']
            if not all(os.path.exists(f'{extract_dir}/datasets/{d}') for d in required_dirs):
                messages.error(request, f"数据集结构无效,停止任务")
                raise ValueError("Invalid dataset structure")
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
            elif sys.platform == "linux":
                print("Training on Linux")
                command = f'yolo train model={trained_model} data=dataset.yaml epochs={task.epochs} imgsz=640 batch=8 pretrained=True'
                screen_name = f"yolo_train_dataset"
                screen_cmd = f"screen -dmS {screen_name} bash -c 'cd {dataset_dir} && {command}'"
                subprocess.run(screen_cmd, shell=True, check=True)
            task.status = 2
            task.save()
            messages.success(request, f"开始执行微调 {task.name} 数据，请耐心等待")
        except Exception as e:
            task.status = 4
            task.save()
    else:
        messages.error(request, f"请勿重复操作！")
    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


def down_model(request, pk):
    trained_path = os.path.join(settings.BASE_DIR, 'runs/detect/train/weights/best.pt')
    if os.path.exists(trained_path):
        response = FileResponse(open(trained_path, 'rb'))
        response['Content-Disposition'] = 'attachment; filename="new_yolo_world.pt"'
        return response
    else:
        messages.error(request, f"新模型训练中，暂未完成，请耐心等待")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))


def down_datasets(request):
    demo_path = os.path.join(settings.BASE_DIR, 'yolo_train_datasets.zip')
    response = FileResponse(open(demo_path, 'rb'))
    response['Content-Disposition'] = 'attachment; filename="yolo_train_datasets.zip"'
    return response


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
                '<a class="el-button el-button--warning el-button--mini" href="{}" style="color: white !important;padding: 4px 5px;"><i class="el-icon-cpu"></i> 训练</a> ',
                reverse('data_train', args=[obj.pk])
            )
        elif obj.status == 2:
            return format_html(
                '<a class="el-button el-button--success el-button--mini" href="{}" style="color: white !important;padding: 4px 5px;"><i class="el-icon-download"></i> 下载</a> ',
                reverse('down_model', args=[obj.pk])
            )

    custom_actions.short_description = '操作'  # 列标题
# Register your models here.
