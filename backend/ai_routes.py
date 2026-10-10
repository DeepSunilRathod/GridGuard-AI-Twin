
from fastapi import APIRouter, HTTPException

from backend.ai_predictor import predictor

router = APIRouter(prefix="/api/ai", tags=["AI Prediction"])


@router.get("/status")
def ai_status():
    return {
        "connected": True,
        "model": "1D CNN + LSTM",
        "sequence_length": 10,
        "features": len(predictor.feature_columns),
        "data_source": "CSV demonstration dataset",
    }


@router.get("/prediction")
def ai_prediction():
    try:
        result = predictor.predict_latest()
        fault_probability = result["fault_probability"]

        # Initial alert threshold for dashboard demonstration.
        # Validate and tune this threshold using held-out data.
        threshold = 0.50

        result["alert"] = fault_probability >= threshold
        result["alert_level"] = (
            "FAULT" if result["alert"] else "NORMAL"
        )
        result["threshold"] = threshold

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI prediction failed: {exc}",
        ) from exc
