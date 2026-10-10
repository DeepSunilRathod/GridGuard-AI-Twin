import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/ai/evaluation", tags=["AI Evaluation"])
PROJECT_ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = PROJECT_ROOT / "ml" / "artifacts" / "evaluation" / "metrics.json"
REPORT_PATH = PROJECT_ROOT / "ml" / "artifacts" / "evaluation" / "classification_report.txt"

@router.get("")
def get_evaluation():
    if not METRICS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Evaluation has not been run yet. Run: python ml\\evaluate_cnn_lstm.py",
        )
    try:
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        if REPORT_PATH.exists():
            metrics["classification_report"] = REPORT_PATH.read_text(encoding="utf-8")
        return metrics
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read evaluation results: {exc}") from exc
