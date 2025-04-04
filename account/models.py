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
