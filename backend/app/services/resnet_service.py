
from pathlib import Path
from functools import lru_cache
import json
from io import BytesIO

import torch
import torch.nn as nn
import torch.nn.functional as F

from PIL import Image
from torchvision import models, transforms


# =========================================================
# PATHS AND CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = BASE_DIR / "models" / "ket_qua_resnet"

MODEL_PATH = MODEL_DIR / "best_model.pth"
MAPPING_PATH = MODEL_DIR / "class_mapping.json"

IMAGE_SIZE = (224, 224)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# =========================================================
# RESNET18 ARCHITECTURE
# =========================================================

class ResNet18Model(nn.Module):
    def __init__(self, num_currencies: int, num_denominations: int):
        super().__init__()

        self.backbone = models.resnet18(weights=None)

        in_features = self.backbone.fc.in_features

        self.backbone.fc = nn.Identity()

        self.currency_head = nn.Linear(
            in_features,
            num_currencies
        )

        self.denomination_head = nn.Linear(
            in_features,
            num_denominations
        )

    def forward(self, x):
        features = self.backbone(x)

        currency_output = self.currency_head(features)
        denomination_output = self.denomination_head(features)

        return currency_output, denomination_output


# =========================================================
# LOAD CLASS MAPPING
# =========================================================

@lru_cache(maxsize=1)
def load_class_mapping():
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy class_mapping.json: {MAPPING_PATH}"
        )

    with open(MAPPING_PATH, "r", encoding="utf-8") as file:
        mapping = json.load(file)

    return mapping


# =========================================================
# LOAD MODEL
# =========================================================

@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy ResNet18 model: {MODEL_PATH}"
        )

    mapping = load_class_mapping()

    model = ResNet18Model(
        num_currencies=mapping["num_currencies"],
        num_denominations=mapping["num_denominations"]
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE
    )

    # Hỗ trợ các định dạng checkpoint phổ biến
    if isinstance(checkpoint, dict):
        if "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        else:
            state_dict = checkpoint
    else:
        raise ValueError("Checkpoint ResNet18 không hợp lệ.")

    # Loại bỏ tiền tố module. nếu model được huấn luyện bằng DataParallel
    cleaned_state_dict = {}

    for key, value in state_dict.items():
        new_key = key.replace("module.", "", 1) if key.startswith("module.") else key
        cleaned_state_dict[new_key] = value

    model.load_state_dict(cleaned_state_dict)

    model.to(DEVICE)
    model.eval()

    return model


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

IMAGE_TRANSFORM = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def preprocess_image(image_bytes: bytes):
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as error:
        raise ValueError("Không thể đọc ảnh được tải lên.") from error

    image_tensor = IMAGE_TRANSFORM(image)

    # Thêm batch dimension và chuyển đến thiết bị chạy model
    image_tensor = image_tensor.unsqueeze(0).to(DEVICE)

    return image_tensor


# =========================================================
# LABEL PARSING
# =========================================================

def parse_denomination_label(label: str):
    parts = str(label).split("_", 1)

    if len(parts) != 2:
        return {
            "currency": None,
            "denomination": None,
            "label": str(label)
        }

    currency = parts[0].upper()

    try:
        denomination = int(parts[1])
    except ValueError:
        denomination = None

    return {
        "currency": currency,
        "denomination": denomination,
        "label": str(label)
    }


# =========================================================
# PREDICTION
# =========================================================

def predict(image_bytes: bytes):
    model = load_model()
    mapping = load_class_mapping()

    image_tensor = preprocess_image(image_bytes)

    with torch.no_grad():
        currency_output, denomination_output = model(image_tensor)

        currency_probabilities = F.softmax(
            currency_output,
            dim=1
        )[0]

        denomination_probabilities = F.softmax(
            denomination_output,
            dim=1
        )[0]

    # -----------------------------------------------------
    # Currency prediction
    # -----------------------------------------------------

    currency_index = int(torch.argmax(currency_probabilities).item())

    currency_classes = mapping["currency_classes"]

    predicted_currency = currency_classes[currency_index]

    currency_confidence = round(
        float(currency_probabilities[currency_index].item()) * 100,
        2
    )

    # -----------------------------------------------------
    # Denomination prediction
    # -----------------------------------------------------

    denomination_classes = mapping["denomination_classes"]

    top_indices = torch.argsort(
        denomination_probabilities,
        descending=True
    )[:3]

    top_predictions = []

    for index_tensor in top_indices:
        index = int(index_tensor.item())

        label = denomination_classes[index]

        info = parse_denomination_label(label)

        top_predictions.append({
            **info,
            "display": mapping["denomination_display"].get(label, label),
            "confidence": round(
                float(denomination_probabilities[index].item()) * 100,
                2
            )
        })

    predicted_index = int(top_indices[0].item())

    predicted_label = denomination_classes[predicted_index]

    predicted_info = parse_denomination_label(predicted_label)

    denomination_confidence = round(
        float(denomination_probabilities[predicted_index].item()) * 100,
        2
    )

    return {
        "currency": predicted_currency,
        "currency_confidence": currency_confidence,

        "denomination": predicted_info["denomination"],
        "denomination_currency": predicted_info["currency"],
        "denomination_label": predicted_label,
        "denomination_display": mapping["denomination_display"].get(
            predicted_label,
            predicted_label
        ),
        "confidence": denomination_confidence,

        "top_predictions": top_predictions
    }
