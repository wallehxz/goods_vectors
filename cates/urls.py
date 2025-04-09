from django.urls import path
from .admin import data_train, down_model, down_datasets, apply_model
urlpatterns = [
    path('yolo_task/<int:pk>/train/', data_train, name='data_train'),
    path('yolo_task/<int:pk>/down_model/', down_model, name='down_model'),
    path('yolo_task/down_datasets', down_datasets, name='down_datasets'),
    path('yolo_task/apply_model', apply_model, name='apply_model'),
]