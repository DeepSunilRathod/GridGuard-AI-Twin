
import sys
from pathlib import Path

# Add the project root to Python's module search path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.ai_predictor import predictor

print("CNN + LSTM model loaded successfully.")
print("Features:", len(predictor.feature_columns))
print("Model input shape:", predictor.model.input_shape)

result = predictor.predict_latest()

print("\nPrediction result:")
for key, value in result.items():
    print(f"{key}: {value}")
