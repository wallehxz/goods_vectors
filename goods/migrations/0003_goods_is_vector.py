# Generated by Django 4.2.20 on 2025-03-24 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_goods_image_url_alter_goods_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='goods',
            name='is_vector',
            field=models.BooleanField(default=False, verbose_name='是否向量'),
        ),
    ]
