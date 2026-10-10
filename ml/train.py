
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix

from model import build_cnn_lstm


# Project paths
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "datasets" / "source" / "Smart Grid Terminal Fault Dataset.csv"
ARTIFACT_DIR = ROOT / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "Fault_Status"
SEQUENCE_LENGTH = 10
RANDOM_STATE = 42


def make_sequences(features, labels, sequence_length):
    X, y = [], []

    for i in range(sequence_length - 1, len(features)):
        X.append(features[i - sequence_length + 1:i + 1])
        y.append(labels[i])

    return np.asarray(X, dtype=np.float32), np.asarray(y, dtype=np.int32)


def main():
    np.random.seed(RANDOM_STATE)
    tf.random.set_seed(RANDOM_STATE)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()

    if TARGET not in df.columns:
        raise ValueError(f"Missing target column: {TARGET}")

    df = df.dropna().reset_index(drop=True)

    # Use numeric sensor/features; exclude the target from inputs.
    feature_columns = [
        column for column in df.select_dtypes(include=np.number).columns
        if column != TARGET
    ]

    if not feature_columns:
        raise ValueError("No numeric feature columns found.")

    X = df[feature_columns].to_numpy(dtype=np.float32)
    y = df[TARGET].to_numpy(dtype=np.int32)

    if not set(np.unique(y)).issubset({0, 1}):
        raise ValueError("Fault_Status must contain binary labels 0 and 1.")

    # Split raw rows first to reduce overlap between training and testing.
    split = int(len(X) * 0.8)
    X_train_raw, X_test_raw = X[:split], X[split:]
    y_train_raw, y_test_raw = y[:split], y[split:]

    if min(len(X_train_raw), len(X_test_raw)) < SEQUENCE_LENGTH:
        raise ValueError("Not enough rows to create sequences.")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_test_scaled = scaler.transform(X_test_raw)

    X_train, y_train = make_sequences(
        X_train_scaled, y_train_raw, SEQUENCE_LENGTH
    )
    X_test, y_test = make_sequences(
        X_test_scaled, y_test_raw, SEQUENCE_LENGTH
    )

    if len(np.unique(y_train)) < 2:
        raise ValueError("Training split must contain both fault classes.")

    classes = np.unique(y_train)
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train
    )
    class_weights = {
        int(label): float(weight)
        for label, weight in zip(classes, weights)
    }

    model = build_cnn_lstm(
        input_shape=(SEQUENCE_LENGTH, len(feature_columns)),
        num_classes=2
    )

    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(ARTIFACT_DIR / "gridguard_cnn_lstm.keras"),
            monitor="val_loss",
            save_best_only=True
        )
    ]

    model.fit(
        X_train,
        y_train,
        validation_split=0.2,
        epochs=30,
        batch_size=32,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1
    )

    probabilities = model.predict(X_test, verbose=0)
    predictions = np.argmax(probabilities, axis=1)

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Normal", "Fault"],
        zero_division=0
    ))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions, labels=[0, 1]))

    joblib.dump(scaler, ARTIFACT_DIR / "scaler.joblib")
    joblib.dump(feature_columns, ARTIFACT_DIR / "feature_columns.joblib")

    metadata = {
        "target": TARGET,
        "sequence_length": SEQUENCE_LENGTH,
        "feature_columns": feature_columns,
        "class_labels": {"0": "Normal", "1": "Fault"},
        "sequence_order_verified": False
    }

    with open(ARTIFACT_DIR / "metadata.json", "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    print("\nTraining complete.")
    print(f"Saved artifacts in: {ARTIFACT_DIR}")
    print("Note: Dataset row order is not verified as true time-series data.")


if __name__ == "__main__":
    main()

