## 商品图片向量搜索

#### 搭建框架 : Python3 Django, SQL: Postgresql, Cache: Redis, Server： Gunicorn
#### 图片识别模型，ResNet50 模型，后台任务 Celery，向量数据库 Milvus, 图片检测：YOLO
#### 用户上传需要检索的图片，先以整张图片作为搜索条件，会将图片检测到的物件单独列出，可以通过物件精准搜索
#### 商品可以后台通过批量上传json文件导入，批量上传的商品所有图片都不会转换向量，需要使用启用后台定时任务处理，
#### 使用堆栈方式把所有向量状态为False的商品一次推送到Redis的列表中，使用多进程逐后台处理，依据自己服务器自定义进程数量，
#### 推荐5个作用，milvus数据库连接池超过10个
#### 图片转向量默认没有使用 TensorFlow keras 的库，如果需要请更改注释依赖,对应模型方法在 ultils/model_tf_resnet50.py
#### 向量数据库需要依赖 docker docker-compose, 服务安装好以后，可以直接在 milvus 文件夹中启用
#### 如果想要使用 显卡进行图片向量 识别，需要搭配 NVIDIA Cuda 12.1 版本
#### CUDA Toolkit 12.1 https://developer.nvidia.com/cuda-12-1-1-download-archive
#### cuDNN 9.1.1       https://developer.nvidia.com/cudnn-9-1-1-download-archive

```
    [{"title": '商品标题', "api_price": 100.10 ,"list_url": 'https://www.example.com/abc.jpg'}]
```
#### 安装依赖库
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    pip3 install -r requirements.txt

#### 向量数据库
    cd milvus && sudo docker-compose up -d

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

