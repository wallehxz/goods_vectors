from django.core.cache import cache
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='名称')
    en_name = models.CharField(max_length=100, null=True, blank=True, unique=True, verbose_name='英文')
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
            existing_categories = set(Category.objects.values_list('en_name', flat=True))
            for item in self.extra.split(','):
                cate = item.strip().lower()
                if cate not in existing_categories:
                    existing_categories.add(cate)
                    cate_list.append(Category(name=cate, en_name=cate))
            if len(cate_list) > 0:
                Category.objects.bulk_create(cate_list)
        else:
            super().save(*args, **kwargs)
        cache.set('cate_list', None)

    @classmethod
    def get_categories(cls):
        return list(Category.objects.values_list('en_name', flat=True))

    @classmethod
    def load_initial_data(cls):
        lists = "smartphone,laptop,headphones,smartwatch,bluetooth speaker,power bank,usb cable,wireless charger,keyboard,mouse,webcam,ssd,router,earbuds,tablet,gaming console,vr headset,drone,action camera,fitness tracker,t-shirt,jeans,sneakers,dress,hoodie,sunglasses,watch,backpack,handbag,belt,scarf,gloves,socks,hat,jacket,swimwear,leggings,necklace,bracelet,earrings,pillow,blanket,coffee maker,blender,air fryer,rice cooker,cutting board,dinnerware set,glassware,kitchen knife,spice rack,towel,curtains,bed sheet,mattress,lamp,wall clock,mirror,flower vase,laundry basket,lipstick,perfume,face cream,shampoo,conditioner,hair dryer,makeup brush,nail polish,razor,toothbrush,sunscreen,face mask,essential oil,body lotion,eyeshadow palette,eyeliner,mascara,foundation,cleanser,makeup mirror,yoga mat,dumbbells,running shoes,bicycle,tent,sleeping bag,hiking backpack,water bottle,ski goggles,tennis racket,basketball,soccer ball,jump rope,resistance bands,camping stove,fishing rod,skateboard,surfboard,gym gloves,badminton set,lego set,board game,puzzle,rc car,doll,stuffed animal,action figure,building blocks,card game,chess set,rubik's cube,water gun,kite,science kit,toy train,fidget spinner,play-doh,magic kit,jigsaw puzzle,nerf gun,car charger,phone holder,seat cover,steering wheel cover,car mat,jump starter,tire pressure gauge,car wax,air freshener,led headlight,car vacuum,bike lock,car organizer,snow chains,dash cam,hitch,roof rack,tool kit,windshield cover,license plate frame,dog food,cat food,pet bed,leash,collar,pet toy,litter box,fish tank,bird cage,grooming brush,pet carrier,chew toy,dog bowl,cat tree,aquarium filter,hamster wheel,reptile heat lamp,flea collar,pet shampoo,training pad,notebook,pen,pencil case,stapler,calculator,desk organizer,file folder,whiteboard,marker,highlighter,eraser,ruler,scissors,glue stick,paper clip,binder,printer,ink cartridge,laptop stand,bookends,thermometer,blood pressure monitor,massage gun,knee brace,first aid kit,heating pad,ice pack,wheelchair,walking cane,compression socks,pill organizer,hand sanitizer,face shield,disposable gloves,nebulizer,orthopedic pillow,acupressure mat,posture corrector,weight scale,yoga block,refrigerator,microwave,oven,toaster,food processor,electric kettle,slow cooker,pressure cooker,juicer,ice cream maker,stand mixer,hand mixer,electric grill,indoor grill,bread maker,egg cooker,vacuum cleaner,robot vacuum,steam mop,washing machine,dryer,washer-dryer combo,handheld vacuum,carpet cleaner,window cleaner,air purifier,dehumidifier,humidifier,fan,air conditioner,electric broom,hair dryer,hair straightener,hair curler,electric shaver,epilator,electric toothbrush,water flosser,facial cleansing brush,foot massager,electric blanket,electric fan,ceiling fan,space heater,iron,steam iron,sewing machine,projector,smart speaker,security camera,doorbell camera,electric fireplace,water dispenser,wine cooler,electric can opener,garlic press,electric knife,food scale,meat grinder,pasta maker,waffle maker,panini press,electric fondue pot,hot plate"
        cate_list = []
        for item in lists:
            cate_list.append(Category(name=item, en_name=item))
        Category.objects.bulk_create(cate_list)


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
