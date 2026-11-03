
from pathlib import Path
from functools import lru_cache

import numpy as np
from PIL import Image
from io import BytesIO
from ultralytics import YOLO


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "ket_qua_yolo"
    / "currency_yolo11n_cls"
    / "weights"
    / "best.pt"
)


# =========================================================
# LOAD MODEL
# =========================================================

@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy YOLO model: {MODEL_PATH}"
        )

    model = YOLO(str(MODEL_PATH))

    return model


# =========================================================
# LABEL PARSING
# =========================================================

def parse_label(label: str):
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
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image_bytes: bytes):
    try:
        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

    except Exception as error:
        raise ValueError(
            "Không thể đọc ảnh được tải lên."
        ) from error

    return image


# =========================================================
# PREDICTION
# =========================================================

def predict(image_bytes: bytes):
    model = load_model()

    image = preprocess_image(image_bytes)

    results = model.predict(
        source=image,
        imgsz=224,
        verbose=False,
        device="cpu"
    )

    if not results:
        raise ValueError("YOLO không trả về kết quả dự đoán.")

    result = results[0]

    if result.probs is None:
        raise ValueError("YOLO không trả về xác suất phân loại.")

    probabilities = result.probs.data.cpu().numpy()

    class_names = result.names

    top_indices = np.argsort(probabilities)[::-1][:3]

    top_predictions = []

    for index in top_indices:
        index = int(index)

        label = class_names[index]

        info = parse_label(label)

        top_predictions.append({
            **info,
            "confidence": round(
                float(probabilities[index]) * 100,
                2
            )
        })

    predicted_index = int(top_indices[0])

    predicted_label = class_names[predicted_index]

    predicted_info = parse_label(predicted_label)

    return {
        **predicted_info,
        "confidence": round(
            float(probabilities[predicted_index]) * 100,
            2
        ),
        "top_predictions": top_predictions
    }
