from django.urls import path

from home import views

urlpatterns = [
    path('', views.index, name='index'),
    path('image_upload', views.image_upload, name='image_upload'),
    path('image_to_vector', views.image_to_vector, name='image_to_vector'),
    path('goods_to_vectors', views.goods_to_vectors, name='goods_to_vectors'),
]