from django.urls import path

from home import views

urlpatterns = [
    path('', views.index, name='index'),
    path('image_upload', views.image_upload, name='image_upload'),
]