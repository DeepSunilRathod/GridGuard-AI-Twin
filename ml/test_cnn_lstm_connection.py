
from backend.ai_predictor import predictor

print("CNN + LSTM model loaded successfully.")
print("Features:", len(predictor.feature_columns))
print("Sequence length:", predictor.model.input_shape)

result = predictor.predict_latest()

print("\nPrediction result:")
for key, value in result.items():
    print(f"{key}: {value}")
