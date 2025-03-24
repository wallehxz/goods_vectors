from django.urls import path
from . import views

urlpatterns = [
    path('get_captcha', views.get_captcha, name='get_captcha'),
    path('login', views.login_user, name='login_user'),
    path('logout', views.logout_user, name='logout_user'),
]