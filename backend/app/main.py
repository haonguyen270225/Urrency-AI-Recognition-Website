
from pathlib import Path
from typing import Callable
import base64
import os

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.prediction_schema import (
    PredictionResponse,
    PredictionResult,
    ModelsResponse,
    ModelInfo,
    HealthResponse
)

from app.services import (
    custom_cnn_service,
    mobilenetv2_service,
    random_forest_service,
    resnet_service,
    yolo_service
)


# =========================================================
# FASTAPI CONFIGURATION
# =========================================================

app = FastAPI(
    title="Currency AI Recognition API",
    description=(
        "API nhận diện tiền tệ USD, CNY, VND "
        "bằng 5 mô hình Machine Learning và Deep Learning."
    ),
    version="1.0.0"
)


# =========================================================
# CORS CONFIGURATION
# =========================================================
# =========================================================
# CORS CONFIGURATION
# =========================================================

LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Read additional frontend origins from environment variables.
# Multiple origins must be separated by commas.
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "")

ALLOWED_ORIGINS = LOCAL_ORIGINS + [
    origin.strip().rstrip("/")
    for origin in FRONTEND_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =========================================================
# MODEL CONFIGURATION
# =========================================================

MODEL_SERVICES: dict[str, Callable] = {
    "custom_cnn": custom_cnn_service.predict,
    "mobilenetv2": mobilenetv2_service.predict,
    "random_forest": random_forest_service.predict,
    "resnet": resnet_service.predict,
    "yolo": yolo_service.predict
}


MODEL_INFORMATION = [
    ModelInfo(
        id="custom_cnn",
        name="Custom CNN",
        description="Mô hình CNN tự xây dựng để nhận diện tiền tệ.",
        input_size="244x244",
        classes=22
    ),
    ModelInfo(
        id="mobilenetv2",
        name="MobileNetV2",
        description="Mô hình CNN nhẹ, sử dụng kiến trúc MobileNetV2.",
        input_size="224x224",
        classes=22
    ),
    ModelInfo(
        id="random_forest",
        name="Random Forest",
        description="Phân loại ảnh xám bằng thuật toán Random Forest.",
        input_size="64x64",
        classes=22
    ),
    ModelInfo(
        id="resnet",
        name="ResNet18",
        description="Mô hình ResNet18 với hai nhánh phân loại.",
        input_size="224x224",
        classes=22
    ),
    ModelInfo(
        id="yolo",
        name="YOLO11",
        description="YOLO11 Classification nhận diện mệnh giá tiền.",
        input_size="224x224",
        classes=22
    )
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp"
}


def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def normalize_prediction(data: dict) -> dict:
    """
    Chuẩn hóa kết quả của 5 service
    thành một cấu trúc thống nhất.
    """

    result = dict(data)

    # Chuẩn hóa top_predictions
    top_predictions = []

    for item in result.get("top_predictions", []):
        item = dict(item)

        item.setdefault("label", None)
        item.setdefault("display", None)
        item.setdefault("currency", None)
        item.setdefault("denomination", None)

        top_predictions.append(item)

    result["top_predictions"] = top_predictions

    # ResNet18 có currency_confidence riêng.
    # Các mô hình còn lại không có trường này.
    result.setdefault("currency_confidence", None)

    return result


async def process_image(
    file: UploadFile,
    model_id: str
) -> PredictionResult:

    filename = file.filename or "uploaded_image"

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng ảnh không được hỗ trợ: {filename}"
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File ảnh rỗng: {filename}"
        )

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Ảnh vượt quá giới hạn 10MB: {filename}"
        )

    predict_function = MODEL_SERVICES[model_id]

    try:
        prediction = predict_function(image_bytes)

        prediction = normalize_prediction(prediction)

        return PredictionResult(
            filename=filename,
            model=model_id,
            denomination_confidence=prediction.get("denomination_confidence"),
            currency=prediction.get("currency"),
            denomination=prediction.get("denomination"),
            confidence=prediction.get("confidence", 0),
            currency_confidence=prediction.get("currency_confidence"),
            denomination_currency=prediction.get("denomination_currency"),
            denomination_label=prediction.get("denomination_label"),
            denomination_display=prediction.get("denomination_display"),
            top_predictions=prediction.get("top_predictions", []),
            image_base64=encode_image(image_bytes)
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi dự đoán ảnh {filename}: {str(error)}"
        ) from error


# =========================================================
# ROUTES
# =========================================================

@app.get(
    "/",
    response_model=HealthResponse,
    tags=["System"]
)
async def root():
    return HealthResponse(
        success=True,
        message="Currency AI Recognition API is running.",
        status="online"
    )


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"]
)
async def health_check():
    return HealthResponse(
        success=True,
        message="Backend is healthy.",
        status="online"
    )


@app.get(
    "/api/models",
    response_model=ModelsResponse,
    tags=["Models"]
)
async def get_models():
    return ModelsResponse(
        success=True,
        models=MODEL_INFORMATION
    )


# =========================================================
# SINGLE IMAGE PREDICTION
# =========================================================

@app.post(
    "/api/predict",
    response_model=PredictionResponse,
    tags=["Prediction"]
)
async def predict_single(
    file: UploadFile = File(...),
    model: str = Form(...)
):

    if model not in MODEL_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình không hợp lệ: {model}"
        )

    result = await process_image(
        file=file,
        model_id=model
    )

    return PredictionResponse(
        success=True,
        message="Dự đoán ảnh thành công.",
        total_images=1,
        results=[result]
    )


# =========================================================
# MULTIPLE IMAGE PREDICTION
# =========================================================

@app.post(
    "/api/predict/batch",
    response_model=PredictionResponse,
    tags=["Prediction"]
)
async def predict_multiple(
    files: list[UploadFile] = File(...),
    model: str = Form(...)
):

    if model not in MODEL_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Mô hình không hợp lệ: {model}"
        )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="Vui lòng tải lên ít nhất một ảnh."
        )

    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Mỗi lần chỉ được tải lên tối đa 20 ảnh."
        )

    results = []

    for file in files:
        result = await process_image(
            file=file,
            model_id=model
        )

        results.append(result)

    return PredictionResponse(
        success=True,
        message="Dự đoán nhiều ảnh thành công.",
        total_images=len(results),
        results=results
    )
