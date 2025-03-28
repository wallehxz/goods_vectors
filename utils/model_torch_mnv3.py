import torch
from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large
from torchvision.io import read_image

# 1. 初始化模型（使用预训练权重）
weights = MobileNet_V3_Large_Weights.IMAGENET1K_V2
model = mobilenet_v3_large(weights=weights)
# 移除分类头，保留特征提取部分
model.classifier = torch.nn.Identity()  # 输出维度: 960 (MobileNetV3-Large的最后一层特征)
model.eval()  # 设置为评估模式
# 2. 定义预处理流程（自动匹配权重对应的标准化参数）
preprocess = weights.transforms()


def image_embedding(image_path):
    img = read_image(image_path)  # 输出格式: CxHxW, 值范围[0, 255]
    img = img[:3, :, :]
    img_tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        features = model(img_tensor)  # 输出: [1, 960]
    return features.squeeze(0).tolist()  # 返回: [960]
