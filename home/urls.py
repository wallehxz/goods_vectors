from django.urls import path

from home import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pdd', views.pdd_index, name='pdd_index'),
    path('pdd_show', views.pdd_show, name='pdd_show'),
    path('image_upload', views.image_upload, name='image_upload'),
    path('image_to_vector', views.image_to_vector, name='image_to_vector'),
    path('pdd_goods_search', views.pdd_goods_search, name='pdd_goods_search'),
    path('pdd_goods_detail', views.pdd_goods_detail, name='pdd_goods_detail'),
    path('pdd_cats_list', views.pdd_cats_list, name='pdd_cats_list'),
    path('goods_to_vectors', views.goods_to_vectors, name='goods_to_vectors'),
    path('set_yolo_model', views.set_yolo_model, name='set_yolo_model'),
    path('web_pdd_search', views.web_pdd_search, name='web_pdd_search'),
    path('web_pdd_detail', views.web_pdd_detail, name='web_pdd_detail'),
]