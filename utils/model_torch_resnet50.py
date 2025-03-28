import torch
import numpy as np
from torchvision.models import resnet50
from torchvision import transforms
from torchvision.io import read_image
from PIL import Image  # 可选，用于加载图片


def image_embedding(image_path):
    model = resnet50(weights='IMAGENET1K_V2')
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
    with torch.no_grad():
        raw_features = model(img_tensor)
    features_np = raw_features.squeeze().numpy()  # 输出形状 (2048,)
    normalized_features = features_np / np.linalg.norm(features_np)
    return normalized_features.tolist()  # 最终格式: List[float]
