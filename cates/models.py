from django.core.cache import cache
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='名称')
    en_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='英文')
    extra = models.TextField(null=True, blank=True,verbose_name='扩展')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'categories'
        verbose_name = '种类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if ',' in self.extra:
            cate_list = []
            for item in self.extra.split(','):
                cate_list.append(Category(name=item, en_name=item))
            Category.objects.bulk_create(cate_list)
        else:
            super().save(*args, **kwargs)
        cache.set('cate_list', None)

    @classmethod
    def get_categories(cls):
        return list(Category.objects.values_list('en_name', flat=True))

    @classmethod
    def load_initial_data(cls):
        Category.objects.bulk_create([
            Category(name="牙刷", en_name="Toothbrush"),
            Category(name="牙膏", en_name="Toothpaste"),
            Category(name="洗发水", en_name="Shampoo"),
            Category(name="沐浴露", en_name="Body Wash"),
            Category(name="肥皂", en_name="Soap"),
            Category(name="卫生纸", en_name="Toilet Paper"),
            Category(name="纸巾", en_name="Paper Towels"),
            Category(name="垃圾袋", en_name="Garbage Bags"),
            Category(name="洗衣液", en_name="Laundry Detergent"),
            Category(name="洗洁精", en_name="Dish Soap"),
            Category(name="海绵", en_name="Sponge"),
            Category(name="洗手液", en_name="Hand Soap"),
            Category(name="护手霜", en_name="Hand Cream"),
            Category(name="防晒霜", en_name="Sunscreen"),
            Category(name="面膜", en_name="Face Mask"),
            Category(name="化妆棉", en_name="Cotton Pads"),
            Category(name="剃须刀", en_name="Razor"),
            Category(name="剃须膏", en_name="Shaving Cream"),
            Category(name="香水", en_name="Perfume"),
            Category(name="指甲剪", en_name="Nail Clipper"),
            Category(name="杯子", en_name="Cup"),
            Category(name="盘子", en_name="Plate"),
            Category(name="碗", en_name="Bowl"),
            Category(name="刀", en_name="Knife"),
            Category(name="叉子", en_name="Fork"),
            Category(name="勺子", en_name="Spoon"),
            Category(name="红酒杯", en_name="Wine Glass"),
            Category(name="茶壶", en_name="Tea Pot"),
            Category(name="煎锅", en_name="Frying Pan"),
            Category(name="砧板", en_name="Cutting Board"),
            Category(name="冰箱", en_name="Refrigerator"),
            Category(name="微波炉", en_name="Microwave"),
            Category(name="烤箱", en_name="Oven"),
            Category(name="搅拌机", en_name="Blender"),
            Category(name="咖啡机", en_name="Coffee Maker"),
            Category(name="椅子", en_name="Chair"),
            Category(name="桌子", en_name="Table"),
            Category(name="床", en_name="Bed"),
            Category(name="书桌", en_name="Desk"),
            Category(name="书架", en_name="Bookcase"),
            Category(name="衣柜", en_name="Wardrobe"),
            Category(name="置物架", en_name="Shelf"),
            Category(name="凳子", en_name="Stool"),
            Category(name="橱柜", en_name="Cabinet"),
            Category(name="电脑", en_name="Computer"),
            Category(name="手机", en_name="Mobile Phone"),
            Category(name="耳机", en_name="Headphones"),
            Category(name="相机", en_name="Camera"),
            Category(name="音箱", en_name="Speaker"),
            Category(name="路由器", en_name="Router"),
            Category(name="智能手表", en_name="Smartwatch"),
            Category(name="平板电脑", en_name="Tablet"),
            Category(name="充电器", en_name="Charger"),
            Category(name="T恤", en_name="T-shirt"),
            Category(name="牛仔裤", en_name="Jeans"),
            Category(name="连衣裙", en_name="Dress"),
            Category(name="夹克", en_name="Jacket"),
            Category(name="运动鞋", en_name="Sneakers"),
            Category(name="凉鞋", en_name="Sandals"),
            Category(name="手提包", en_name="Handbag"),
            Category(name="双肩包", en_name="Backpack"),
            Category(name="太阳镜", en_name="Sunglasses"),
            Category(name="皮带", en_name="Belt"),
            Category(name="钢笔", en_name="Pen"),
            Category(name="铅笔", en_name="Pencil"),
            Category(name="笔记本", en_name="Notebook"),
            Category(name="订书机", en_name="Stapler"),
            Category(name="文件夹", en_name="Folder"),
            Category(name="计算器", en_name="Calculator"),
            Category(name="打印机", en_name="Printer"),
            Category(name="扫描仪", en_name="Scanner"),
            Category(name="白板", en_name="Whiteboard"),
            Category(name="信封", en_name="Envelope"),
            Category(name="台灯", en_name="Lamp"),
            Category(name="镜子", en_name="Mirror"),
            Category(name="窗帘", en_name="Curtain"),
            Category(name="地毯", en_name="Rug"),
            Category(name="花瓶", en_name="Vase"),
            Category(name="蜡烛", en_name="Candle"),
            Category(name="相框", en_name="Picture Frame"),
            Category(name="挂钟", en_name="Wall Clock"),
            Category(name="花盆", en_name="Flower Pot"),
            Category(name="抱枕", en_name="Throw Pillow"),
            Category(name="篮球", en_name="Basketball"),
            Category(name="足球", en_name="Football"),
            Category(name="网球拍", en_name="Tennis Racket"),
            Category(name="瑜伽垫", en_name="Yoga Mat"),
            Category(name="哑铃", en_name="Dumbbell"),
            Category(name="帐篷", en_name="Tent"),
            Category(name="睡袋", en_name="Sleeping Bag"),
            Category(name="自行车", en_name="Bicycle"),
            Category(name="滑板", en_name="Skateboard"),
            Category(name="鱼竿", en_name="Fishing Rod"),
            Category(name="玩偶", en_name="Doll"),
            Category(name="手办", en_name="Action Figure"),
            Category(name="桌游", en_name="Board Game"),
            Category(name="拼图", en_name="Puzzle"),
            Category(name="帽子", en_name="Hat"),
            Category(name="鞋子", en_name="Shoes"),
            Category(name="吹风机", en_name="Hair dryer"),
            Category(name="筷子", en_name="Chopsticks"),
            Category(name="书", en_name="Book"),
            Category(name="包", en_name="Bag"),
            Category(name="泰迪熊", en_name="Teddy bear"),
            Category(name="剪刀", en_name="Scissors"),
            Category(name="剪刀", en_name="Scissors"),
            Category(name="水槽", en_name="Sink"),
            Category(name="烤面包机", en_name="Toaster"),
            Category(name="鼠标", en_name="Mouse"),
            Category(name="键盘", en_name="Keyboard"),
            Category(name="遥控器", en_name="Remote"),
            Category(name="笔记本电脑", en_name="Laptop"),
            Category(name="电视", en_name="TV"),
            Category(name="餐桌", en_name="Dining Table"),
            Category(name="盆栽", en_name="Potted Plant"),
            Category(name="沙发", en_name="Couch"),
            Category(name="椅子", en_name="Chair"),
            Category(name="瓶子", en_name="Bottle"),
            Category(name="伞", en_name="Umbrella"),
            Category(name="领带", en_name="Tie"),
            Category(name="手提箱", en_name="Suitcase"),
            Category(name="飞盘", en_name="Frisbee"),
            Category(name="滑雪板", en_name="Skis"),
            Category(name="滑雪板", en_name="Snowboard"),
            Category(name="运动球", en_name="Sports Ball"),
            Category(name="风筝", en_name="Kite"),
            Category(name="棒球棒", en_name="Baseball Bat"),
            Category(name="棒球手套", en_name="Baseball Glove"),
            Category(name="滑板", en_name="Skateboard"),
            Category(name="冲浪板", en_name="Surfboard"),
            Category(name="西装", en_name="Suit"),
            Category(name="手套", en_name="Gloves"),
            Category(name="眼镜", en_name="Spectacles"),
            Category(name="口红", en_name="Lipstick"),
            Category(name="胸罩", en_name="Bra"),
            Category(name="内衣", en_name="Underwear"),
            Category(name="服装", en_name="Clothing"),
            Category(name="腰带", en_name="Belt"),
            Category(name="面包", en_name="Bread"),
            Category(name="门", en_name="Door"),
            Category(name="玻璃", en_name="Glass"),
            Category(name="洗碗机", en_name="Dishwasher"),
            Category(name="橱柜", en_name="Cabinet"),
            Category(name="篮球", en_name="Basketball"),
            Category(name="足球", en_name="Football"),
            Category(name="羽毛球", en_name="Badminton"),
            Category(name="梳子", en_name="Comb"),
            Category(name="运动内衣", en_name="Sportswear"),
            Category(name="人", en_name="Person"),
            Category(name="空调", en_name="Air Conditioner"),
            Category(name="乐高", en_name="Lego")
        ])


class YoloTask(models.Model):
    STATE = ((1, 'Pending'), (2, 'Training'), (3, 'Completed'), (4, 'Canceled'))

    name = models.CharField(max_length=100, verbose_name='名称')
    data_zip = models.FileField(upload_to='dataset/', verbose_name='数据集')
    trained_model = models.FileField(upload_to='yolo_models', null=True, blank=True, verbose_name='微调模型')
    status = models.IntegerField(choices=STATE, default=1, verbose_name='状态')
    epochs = models.IntegerField(default=10, verbose_name='迭代轮次')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'yolo_tasks'
        verbose_name = '模型微调'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
