## 商品图片向量搜索；商品识别裁剪；识别模型训练优化

#### 搭建框架 : Python3 Django, SQL: Postgresql, Cache: Redis, Server： Gunicorn
#### 图片识别模型，ResNet50 模型，后台任务 Celery，向量数据库 Milvus, 图片检测：ultralytics YOLO
#### 图片识别去重 imagehash.phash
#### 用户上传需要检索的图片，先以整张图片作为搜索条件，会将图片检测到的物件单独列出，可以通过物件精准搜索
#### 对上传的图片进行识别裁剪，可以选择对应的物品图片进行二次检索，后台有对应的类别白名单，在白名单中进行图片识别
#### 商品可以后台通过批量上传json文件导入，批量上传的商品所有图片都不会转换向量，需要使用启用后台定时任务处理，
#### 使用堆栈方式把所有向量状态为False的商品一次推送到Redis的列表中，使用多进程逐后台处理，依据自己服务器自定义进程数量，
#### 推荐5个作用，milvus数据库连接池超过10个
#### 图片转向量默认没有使用 TensorFlow keras 的库，如果需要请更改注释依赖,对应模型方法在 ultils/model_tf_resnet50.py
#### 向量数据库需要依赖 docker docker-compose, 服务安装好以后，可以直接在 milvus 文件夹中启用
#### 如果想要使用 显卡进行图片向量 识别，需要搭配 NVIDIA Cuda 12.1 版本
#### CUDA Toolkit 12.1 https://developer.nvidia.com/cuda-12-1-1-download-archive
#### cuDNN 9.1.1       https://developer.nvidia.com/cudnn-9-1-1-download-archive
#### 由于预训练的模型识别物体有限，新增微调模型功能，对于新的物品，推荐使用 label-studio 进行图片标注导出，图片数量 300 - 500；
#### 导出的数据格式 Yolo image，可以直接上传模型训练，会自动构建文件包
#### label-studio https://labelstud.io/guide/quick_start

```
    [{"title": '商品标题', "price": 100.00 ,"image_url": 'https://www.example.com/abc.jpg'}]
```
#### 安装依赖库
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    pip install ftfy regex tqdm
    pip install git+https://gitee.com/zalle/clip.git
    pip3 install -r requirements.txt

#### 模型训练
    https://docs.ultralytics.com/zh/modes/train/#usage-examples
    yolo train data=dataset.yaml model=yolov11n.pt epochs=10 imgsz=640 batch=8 pretrained=True

#### 向量数据库
    cd milvus && sudo docker-compose up -d

#### 迁移数据库
    python3.9 manage.py makemigrations
    python3.9 manage.py migrate

#### 初始化数据
    添加管理账号
    python3.9 manage.py createsuperuser root
    初始化图片类别 使用 python manage.py shell 执行
    Category.load_initial_data()

#### 任务管理
    #windows 使用单进程模式
    celery -A main worker --pool=solo --loglevel=info

    # 启动 Celery Worker
    celery -A main worker --loglevel=info

    # 启动 Celery Beat
    celery -A main beat --loglevel=info

#### 启动项目

    python3.9 manage.py runserver
    
    gunicorn main.wsgi:applitcation

