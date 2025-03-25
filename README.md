## 商品图片向量搜索

#### 搭建框架 : Python3 Django, SQL: Postgresql, Cache: Redis, Server： Gunicorn
#### 图片识别模型，ResNet50 模型，后台任务 Celery，向量数据库 Milvus
#### 商品可以通过批量上传json文件导入，批量上传的商品所有图片都不会转换向量，需要使用启用后台定时任务处理，
#### 使用堆栈方式把所有向量状态为False的商品一次推送到Redis的列表中，使用多进程逐个处理
```
    [{"title": '商品标题', "api_price": 100.10 ,"list_url": 'https://www.example.com/abc.jpg'}]
```
#### 商品图片向量搜索

    pip3 install -r requirements.txt

#### 迁移数据库
    python3.10 manage.py makemigrations
    python3.10 manage.py migrate

#### 添加管理员

    python3.10 manage.py createsuperuser root

#### 任务管理
    #windows 使用单进程模式
    celery -A main worker --pool=solo --loglevel=info

    # 启动 Celery Worker
    celery -A main worker --loglevel=info

    # 启动 Celery Beat
    celery -A main beat --loglevel=info

#### 启动项目

    python3.10 manage.py runserver
    
    gunicorn main.wsgi:applitcation

