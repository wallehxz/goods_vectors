# Generated by Django 4.2.20 on 2025-04-12 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goods", "0005_goods_goods_id_bd961a_idx_goods_name_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255, verbose_name="标题")),
                ("list_url", models.CharField(max_length=350, verbose_name="图片")),
                ("api_price", models.FloatField(verbose_name="价格")),
            ],
            options={
                "verbose_name": "图片",
                "verbose_name_plural": "图片",
                "db_table": "product",
                "managed": False,
            },
        ),
        migrations.AlterModelOptions(
            name="goods",
            options={"verbose_name": "商品", "verbose_name_plural": "商品"},
        ),
    ]
