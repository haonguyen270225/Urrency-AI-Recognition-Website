
from pathlib import Path
import json
from functools import lru_cache

import cv2
import numpy as np
import tensorflow as tf


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_DIR = BASE_DIR / "models" / "ket_qua_custom_cnn"

MODEL_PATH = MODEL_DIR / "best_custom_cnn.keras"
CLASS_NAMES_PATH = MODEL_DIR / "class_names.json"


# =========================================================
# LABEL MAPPING
# =========================================================

LABEL_MAPPING = {
    # USD
    "1 dollar": ("USD", 1),
    "2 doolar": ("USD", 2),
    "5 dollar": ("USD", 5),
    "10 dollar": ("USD", 10),
    "20 dollar": ("USD", 20),
    "50 dollar": ("USD", 50),
    "100 dollar": ("USD", 100),

    # CNY
    "1": ("CNY", 1),
    "5": ("CNY", 5),
    "10": ("CNY", 10),
    "20": ("CNY", 20),
    "50": ("CNY", 50),
    "100": ("CNY", 100),

    # VND
    "001000": ("VND", 1000),
    "002000": ("VND", 2000),
    "005000": ("VND", 5000),
    "010000": ("VND", 10000),
    "020000": ("VND", 20000),
    "050000": ("VND", 50000),
    "100000": ("VND", 100000),
    "200000": ("VND", 200000),
    "500000": ("VND", 500000),
}


# =========================================================
# LOAD MODEL
# =========================================================

@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy Custom CNN model: {MODEL_PATH}"
        )

    model = tf.keras.models.load_model(
        MODEL_PATH,
        compile=False
    )

    return model


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

    # BGR -> RGB
    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    # Lấy kích thước trực tiếp từ model
    model = load_model()

    height = model.input_shape[1]
    width = model.input_shape[2]

    image = cv2.resize(
        image,
        (width, height)
    )

    # Chuẩn hóa giống cách huấn luyện Custom CNN
    image = image.astype(np.float32) / 255.0

    # Thêm batch dimension
    image = np.expand_dims(image, axis=0)

    return image


# =========================================================
# LABEL PARSING
# =========================================================

def parse_label(label: str):
    normalized_label = str(label).strip().lower()

    result = LABEL_MAPPING.get(normalized_label)

    if result is None:
        return {
            "currency": None,
            "denomination": None,
            "label": str(label)
        }

    currency, denomination = result

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
            "Số lượng đầu ra của model không khớp class_names.json."
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
