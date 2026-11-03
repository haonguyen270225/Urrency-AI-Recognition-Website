
from typing import Optional
from pydantic import BaseModel
denomination_confidence: Optional[float] = None

class TopPrediction(BaseModel):
    currency: Optional[str] = None
    denomination: Optional[int] = None
    label: Optional[str] = None
    display: Optional[str] = None
    confidence: float


class PredictionResult(BaseModel):
    filename: str
    model: str

    currency: Optional[str] = None
    denomination: Optional[int] = None

    confidence: float

    currency_confidence: Optional[float] = None
    denomination_currency: Optional[str] = None
    denomination_label: Optional[str] = None
    denomination_display: Optional[str] = None

    top_predictions: list[TopPrediction]

    image_base64: str


class PredictionResponse(BaseModel):
    success: bool
    message: str
    total_images: int
    results: list[PredictionResult]


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    input_size: str
    classes: int


class ModelsResponse(BaseModel):
    success: bool
    models: list[ModelInfo]


class HealthResponse(BaseModel):
    success: bool
    message: str
    status: str
