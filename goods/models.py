import uuid
import os
import time
import aiohttp
import asyncio
from django.db import models
import requests
from django.conf import settings
if settings.MILVUS_DATA == '960_collection':
    from utils.milvus_960_collection import collection
else:
    from utils.milvus_2048_collection import collection

def save_vector(goods_id, embedding):
    # 插入向量
    entities = [
        [goods_id],  # 主键
        [embedding]  # 向量
    ]
    collection.insert(entities)
    collection.flush()

def delete_vector(goods_id):
    expr = f'goods_id == {goods_id}'
    delete_result = collection.delete(expr)
    collection.release()
    print('Milrus delete goods id', goods_id)

def get_vector(goods_id):
    collection.load()
    expr = f'goods_id == {goods_id}'
    output_fields = ["goods_id", "embedding"]
    result = collection.query(expr, output_fields=output_fields)
    if len(result) > 0:
        return result[0]['embedding']

class Goods(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name='商品名称')
    price = models.FloatField(null=True, blank=True,verbose_name='价格')
    image = models.ImageField(upload_to='goods/%Y%m%d/', null=True, blank=True,verbose_name='图片文件')
    image_url = models.CharField(max_length=500, null=True, blank=True,verbose_name='图片链接')
    is_vector = models.BooleanField(default=False, verbose_name='图片向量')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'goods'
        verbose_name = '商品'
        verbose_name_plural = verbose_name

        indexes = [
            models.Index(fields=['id', 'name']),  # 复合索引
            models.Index(fields=['name'], name='name_idx'),  # 单独索引
        ]

    def __str__(self):
        return self.name

    def get_vector_shape(self):
        vector = get_vector(self.id)
        return f'(Dim[{len(vector)}], Sum[{int(sum(vector))}])'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if self.has_image():
            try:
                if is_new:
                    image_path = self.image_path()
                    embedding = Goods.image_to_embedding(image_path)
                    save_vector(self.id, embedding)
                    self.is_vector = True
                    self.save()
                else:
                    if self.check_by_embedding() is False:
                        image_path = self.image_path()
                        embedding = Goods.image_to_embedding(image_path)
                        save_vector(self.id, embedding)
                        self.is_vector = True
                        self.save()
            except Exception as e:
                print(e)

    def delete_vector(self):
        if self.check_by_embedding():
            delete_vector(self.id)

    def update_vector(self):
        if self.is_vector == False:
            if self.check_by_embedding():
                self.is_vector = True
                self.save()
        elif self.has_image() and self.check_by_embedding() == False:
            image_path = self.image_path()
            embedding = Goods.image_to_embedding(image_path)
            save_start = time.perf_counter()
            save_vector(self.id, embedding)
            save_end = time.perf_counter()
            print(f'save to milrus vector time: {save_end - save_start}')
            if self.is_vector == False:
                self.is_vector = True
                self.save()


    def delete(self, *args, ** kwargs):
        if self.check_by_embedding():
            delete_vector(self.id)
        super().delete(*args, ** kwargs)


    def has_image(self) -> bool:
        if self.image_url is not None:
            return True
        elif self.image and self.image.url:
            return True
        else:
            return False

    @classmethod
    async def temp_image_path(cls, image_url, file_name=None, base_dir='temps'):
        try:
            temp_dir = os.path.join(settings.MEDIA_ROOT, base_dir)
            os.makedirs(temp_dir, exist_ok=True)  # 确保目录存在
            if file_name:
                temp_path = os.path.join(temp_dir, file_name)
                if os.path.exists(temp_path):
                    print(f'file {temp_path} already exists, no request')
                    return temp_path
            else:
                temp_path = os.path.join(temp_dir, f'{uuid.uuid4()}.jpg')

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Cache-Control": "no-cache",
                "Sec-Ch-Ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                "Upgrade-Insecure-Requests": "1",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, headers=headers, timeout=10) as response:
                    response.raise_for_status()  # 检查请求是否成功
                    with open(temp_path, 'wb') as f:
                        f.write(await response.read())
            return temp_path
        except requests.exceptions.RequestException as e:
            print(f"Error：{e}")
            return None

    def image_path(self):
        if self.image_url is not None:
            return asyncio.run(Goods.temp_image_path(self.image_url, file_name=f'goods_{self.id}.jpg'))
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
    def similar_vectors(cls, query_embedding, top_k=21):
        # 搜索 HNSW 相似向量, ef 的数值 应为 大于 2 * top_k
        # 搜索 IVF_FLAT 相似向量, nprobe 的数值 应为 nlist 的 5% ~ 10%
        if settings.MILVUS_DATA == '960_collection':
            search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
        else:
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 1024 }}
        collection.load()
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
    def image_to_embedding(cls, image_path):
        start = time.perf_counter()
        if settings.EMBEDDING_MODEL == 'torch_mnv3':
            from utils.model_torch_mnv3 import image_embedding as mnv3_embedding
            embedding = mnv3_embedding(image_path)
        else:
            from utils.model_torch_resnet50 import image_embedding as trn50_embedding
            embedding = trn50_embedding(image_path)
        end = time.perf_counter()
        print(f'{image_path} embedding time: {end - start}')
        return embedding


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name='标题')
    list_url = models.CharField(max_length=350, verbose_name='图片')
    api_price = models.FloatField(verbose_name='价格')

    class Meta:
        managed = False
        db_table = 'product'
        verbose_name = '图片'
        verbose_name_plural = verbose_name