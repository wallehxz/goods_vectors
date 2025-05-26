import random
from django.db import models
from django.contrib.auth.models import AbstractUser


class Consumer(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True, null=True, blank=True, verbose_name='手机号')

    def __str__(self):
        return self.username

    def role_display(self):
        if self.is_superuser:
            return '超级管理员'
        elif self.is_staff:
            return '员工'
        else:
            return '消费者'


class PddUser(models.Model):
    mobile = models.CharField(max_length=11, unique=True, null=True, blank=True, verbose_name='手机号')
    sms_code = models.CharField(max_length=6, null=True, blank=True, verbose_name='短信验证码')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'pdd_users'
        verbose_name = '拼多多账户'
        verbose_name_plural = verbose_name