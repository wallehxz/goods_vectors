import uuid
import os
from django.db import models
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from keras.models import Model
import numpy as np
from PIL import Image
import torch.nn as nn
import torch
from torchvision import models as tmodels, transforms
from goods.milvus_client import collection
import requests
from django.conf import settings

def save_vector(goods_id, embedding):
    # 插入向量
    entities = [
        [goods_id],  # 主键
        [embedding]  # 向量
    ]
    collection.insert(entities)
    collection.flush()

class Goods(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name='商品名称')
    price = models.FloatField(null=True, blank=True,verbose_name='价格')
    image = models.ImageField(upload_to='goods/%Y%m%d/', null=True, blank=True,verbose_name='图片文件')
    image_url = models.CharField(max_length=245, null=True, blank=True,verbose_name='图片链接')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'goods'
        verbose_name = '商品表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if self.has_image():
            if is_new:
                image_path = self.image_path()
                embedding = Goods.get_resnet_vector(image_path)
                save_vector(self.id, embedding)
            else:
                if self.check_by_embedding() is False:
                    image_path = self.image_path()
                    embedding = Goods.get_resnet_vector(image_path)
                    save_vector(self.id, embedding)

    def has_image(self) -> bool:
        if self.image_url is not None:
            return True
        elif self.image and self.image.url:
            return True
        else:
            return False

    def image_path(self):
        if self.image_url is not None:
            try:
                response = requests.get(self.image_url, timeout=10)
                response.raise_for_status()  # 检查请求是否成功
                temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
                os.makedirs(temp_dir, exist_ok=True)  # 确保目录存在
                temp_path = os.path.join(temp_dir, f'{uuid.uuid4()}.jpg')
                with open(temp_path, 'wb+') as destination:
                    destination.write(response.content)
                return temp_path
            except requests.exceptions.RequestException as e:
                print(f"Error：{e}")
        elif self.image and self.image.url:
            return self.image.path

    def check_by_embedding(self) -> bool:
        collection.load()
        # 精确查询业务ID
        expr = f'goods_id == {self.id}'
        result = collection.query(
            expr=expr,
            output_fields=["id"]
        )
        return len(result) > 0


    @classmethod
    def similar_vectors(cls, query_embedding, top_k=10):
        # 搜索相似向量
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 128}}
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["goods_id"],
        )
        # 返回相似向量的 ID
        return [
            (hit.entity.get("goods_id"), 1 - hit.distance)  # 转换相似度为分数
            for hit in results[0]
        ]


    @classmethod
    def image_to_vector(cls, image_path):
        base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
        model = Model(inputs=base_model.input, outputs=base_model.output)
        img = Image.open(image_path).convert('RGB')
        img = img.resize((224, 224))  # ResNet的输入尺寸
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)  # 应用模型特定的预处理
        # 提取特征向量
        # print(model.summary())
        vector = model.predict(img_array)
        # vector_tensor = torch.from_numpy(vector).float()
        # print("原始维度：", vector.shape)
        # fc_layer = nn.Linear(2048, 512)
        # reduced_vector = fc_layer(vector_tensor)
        # print("降维：", reduced_vector.shape)
        return vector.flatten().tolist()


    @classmethod
    def get_resnet_vector(cls, image_path):
        # 加载模型
        model = tmodels.resnet50(weights='IMAGENET1K_V1')
        model = torch.nn.Sequential(*(list(model.children())[:-1]))
        model.eval()
        # 预处理
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        img = Image.open(image_path).convert("RGB")
        img_tensor = preprocess(img).unsqueeze(0)
        # 提取特征
        with torch.no_grad():
            raw_features = model(img_tensor)
        features_np = raw_features.squeeze().numpy()  # 输出形状 (2048,)
        # L2 归一化（关键步骤）
        normalized_features = features_np / np.linalg.norm(features_np)
        # 转换为 Python list 格式（Milvus 要求）
        return normalized_features.tolist()  # 最终格式: List[float]