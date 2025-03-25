import os
from celery import Celery
import django

# 设置 Django 的默认配置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()
app = Celery('main')
# 使用 Django 的配置文件
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

