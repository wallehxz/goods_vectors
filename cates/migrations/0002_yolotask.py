# Generated by Django 4.2.20 on 2025-04-06 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cates", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="YoloTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="名称")),
                (
                    "data_zip",
                    models.FileField(upload_to="dataset/", verbose_name="数据集"),
                ),
                (
                    "trained_model",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="yolo_models",
                        verbose_name="微调模型",
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (1, "pending"),
                            (2, "training"),
                            (3, "completed"),
                            (4, "cancelled"),
                        ],
                        default=1,
                        verbose_name="状态",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "模型微调",
                "verbose_name_plural": "模型微调",
                "db_table": "yolo_tasks",
            },
        ),
    ]
