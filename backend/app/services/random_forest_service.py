
from pathlib import Path
from functools import lru_cache

import cv2
import joblib
import numpy as np


# =========================================================
# PATHS AND CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "ket_qua_random_forset"
    / "rf_currency_classifier.pkl"
)

IMAGE_SIZE = (64, 64)


# =========================================================
# LOAD MODEL
# =========================================================

@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy Random Forest model: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


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
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise ValueError("Không thể đọc ảnh được tải lên.")

    # Resize giống quá trình huấn luyện
    image = cv2.resize(
        image,
        IMAGE_SIZE
    )

    # Flatten thành vector 4096 đặc trưng
    image = image.flatten()

    return np.asarray(
        [image],
        dtype=np.uint8
    )


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
# PREDICTION
# =========================================================

def predict(image_bytes: bytes):
    model = load_model()

    input_data = preprocess_image(image_bytes)

    predicted_label = model.predict(input_data)[0]

    predicted_info = parse_label(predicted_label)

    if not hasattr(model, "predict_proba"):
        raise ValueError(
            "Random Forest model không hỗ trợ predict_proba."
        )

    probabilities = model.predict_proba(input_data)[0]

    top_indices = np.argsort(probabilities)[::-1][:3]

    top_predictions = []

    for index in top_indices:
        label = model.classes_[index]

        info = parse_label(label)

        top_predictions.append({
            **info,
            "confidence": round(
                float(probabilities[index]) * 100,
                2
            )
        })

    return {
        **predicted_info,
        "confidence": round(
            float(np.max(probabilities)) * 100,
            2
        ),
        "top_predictions": top_predictions
    }
