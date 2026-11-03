
from pathlib import Path
import json
from functools import lru_cache

import cv2
import numpy as np
import tensorflow as tf

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = BASE_DIR / "models" / "ket_qua_mobilenetv2"

MODEL_PATH = MODEL_DIR / "mobilenetv2_currency_denomination.keras"
CLASS_NAMES_PATH = MODEL_DIR / "class_names.json"

IMAGE_SIZE = (224, 224)


# =========================================================
# LOAD MODEL
# =========================================================

@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy MobileNetV2 model: {MODEL_PATH}"
        )

    return tf.keras.models.load_model(
        MODEL_PATH,
        compile=False
    )


@lru_cache(maxsize=1)
def load_class_names():
    if not CLASS_NAMES_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy class_names.json: {CLASS_NAMES_PATH}"
        )

    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image_bytes: bytes):
    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise ValueError("Không thể đọc ảnh được tải lên.")

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    image = image.astype(np.float32)

    image = preprocess_input(image)

    image = np.expand_dims(
        image,
        axis=0
    )

    return image


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

    currency_mapping = {
        "AmericanDollar": "USD",
        "ChineseYuan": "CNY",
        "VietnameseDong": "VND"
    }

    currency = currency_mapping.get(parts[0])

    denomination_label = parts[1].strip().lower()

    try:
        denomination = int(denomination_label)
    except ValueError:
        denomination_mapping = {
            "1 dollar": 1,
            "2 doolar": 2,
            "5 dollar": 5,
            "10 dollar": 10,
            "20 dollar": 20,
            "50 dollar": 50,
            "100 dollar": 100
        }

        denomination = denomination_mapping.get(
            denomination_label
        )

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
    class_names = load_class_names()

    image = preprocess_image(image_bytes)

    predictions = model.predict(
        image,
        verbose=0
    )[0]

    if len(predictions) != len(class_names):
        raise ValueError(
            "Số lượng đầu ra không khớp class_names.json."
        )

    top_indices = np.argsort(predictions)[::-1][:3]

    predicted_index = int(top_indices[0])

    predicted_label = class_names[predicted_index]

    predicted_info = parse_label(predicted_label)

    top_predictions = []

    for index in top_indices:
        index = int(index)

        label = class_names[index]
        info = parse_label(label)

        top_predictions.append({
            **info,
            "confidence": round(
                float(predictions[index]) * 100,
                2
            )
        })

    return {
        **predicted_info,
        "confidence": round(
            float(predictions[predicted_index]) * 100,
            2
        ),
        "top_predictions": top_predictions
    }
