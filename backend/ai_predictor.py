
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = PROJECT_ROOT / "ml" / "artifacts"
DATASET_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "source"
    / "Smart Grid Terminal Fault Dataset.csv"
)

MODEL_PATH = MODEL_DIR / "gridguard_cnn_lstm.keras"
SCALER_PATH = MODEL_DIR / "scaler.joblib"
FEATURES_PATH = MODEL_DIR / "feature_columns.joblib"

SEQUENCE_LENGTH = 10


class CNNLSTMPredictor:
    def __init__(self):
        required_files = [
            MODEL_PATH,
            SCALER_PATH,
            FEATURES_PATH,
            DATASET_PATH,
        ]

        missing = [str(p) for p in required_files if not p.exists()]
        if missing:
            raise FileNotFoundError(
                "Required GridGuard files not found: "
                + ", ".join(missing)
            )

        self.model = load_model(MODEL_PATH, compile=False)
        self.scaler = joblib.load(SCALER_PATH)
        self.feature_columns = list(joblib.load(FEATURES_PATH))

        if len(self.feature_columns) != 14:
            raise ValueError(
                f"Expected 14 features, got {len(self.feature_columns)}"
            )

    def predict_latest(self):
        # Load dataset
        df = pd.read_csv(DATASET_PATH)

        missing_columns = [
            col for col in self.feature_columns
            if col not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Dataset is missing columns: {missing_columns}"
            )

        if len(df) < SEQUENCE_LENGTH:
            raise ValueError(
                f"At least {SEQUENCE_LENGTH} rows are required"
            )

        # Select features in the exact training order
        features = df[self.feature_columns].tail(
            SEQUENCE_LENGTH
        )

        features = features.apply(
            pd.to_numeric, errors="raise"
        )

        scaled = self.scaler.transform(features)

        # Expected CNN + LSTM input: (batch, 10 timesteps, 14 features)
        sequence = np.expand_dims(scaled, axis=0)

        output = np.asarray(
            self.model.predict(sequence, verbose=0)
        ).reshape(-1)

        if output.size == 1:
            fault_probability = float(output[0])
        elif output.size == 2:
            # Assumes the training class order is [normal, fault].
            fault_probability = float(output[1])
        else:
            raise ValueError(
                f"Unexpected model output shape: {output.shape}"
            )

        fault_probability = float(
            np.clip(fault_probability, 0.0, 1.0)
        )

        return {
            "predicted_label": (
                "FAULT" if fault_probability >= 0.5 else "NORMAL"
            ),
            "fault_probability": round(fault_probability, 4),
            "normal_probability": round(
                1.0 - fault_probability, 4
            ),
            "sequence_length": SEQUENCE_LENGTH,
            "features_used": len(self.feature_columns),
            "note": (
                "CSV dataset demonstration using the last 10 rows; "
                "not a live simulator prediction."
            ),
        }


predictor = CNNLSTMPredictor()
