# import numpy as np
# from PIL import Image
# from tensorflow.keras import Model
# from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
#
#
# def image_embedding(image_path):
#     base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
#     model = Model(inputs=base_model.input, outputs=base_model.output)
#     img = Image.open(image_path).convert('RGB')
#     img = img.resize((224, 224))  # ResNet的输入尺寸
#     img_array = np.array(img)
#     img_array = np.expand_dims(img_array, axis=0)
#     img_array = preprocess_input(img_array)  # 应用模型特定的预处理
#     vector = model.predict(img_array)
#     return vector.flatten().tolist()
