from django.urls import path
from .admin import down_model, apply_model, build_train
urlpatterns = [
    path('yolo_task/<int:pk>/down_model/', down_model, name='down_model'),
    path('yolo_task/apply_model', apply_model, name='apply_model'),
    path('yolo_task/<int:pk>/build_train', build_train, name='build_train'),
]