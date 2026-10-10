from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, balanced_accuracy_score
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "ml" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "gridguard_cnn_lstm.keras"
SCALER_PATH = ARTIFACT_DIR / "scaler.joblib"
FEATURES_PATH = ARTIFACT_DIR / "feature_columns.joblib"
DATASET_PATH = PROJECT_ROOT / "datasets" / "source" / "Smart Grid Terminal Fault Dataset.csv"
OUTPUT_DIR = ARTIFACT_DIR / "evaluation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SEQUENCE_LENGTH = 10
TARGET_COLUMN = "Fault_Status"

def main():
    for path in [MODEL_PATH, SCALER_PATH, FEATURES_PATH, DATASET_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    df = pd.read_csv(DATASET_PATH)
    df.columns = df.columns.str.strip()
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Dataset target '{TARGET_COLUMN}' not found.")
    feature_columns = list(joblib.load(FEATURES_PATH))
    missing = [c for c in feature_columns + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing dataset columns: {missing}")

    # Reproduce the common row-order sequence construction, but explicitly warn
    # that the CSV has no verified timestamp/asset sequence.
    features = df[feature_columns].apply(pd.to_numeric, errors="coerce")
    labels = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
    valid = features.notna().all(axis=1) & labels.notna()
    features = features.loc[valid].reset_index(drop=True)
    labels = labels.loc[valid,].astype(int).reset_index(drop=True)
    if len(features) <= SEQUENCE_LENGTH:
        raise ValueError("Not enough rows to form sequences.")

    scaler = joblib.load(SCALER_PATH)
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)

    # Evaluate a final chronological 20% of constructed windows.
    # This is only a provisional evaluation because CSV row order is not verified
    # as temporal and the training split strategy may differ.
    X, y = [], []
    arr = features.to_numpy(dtype=np.float32)
    lab = labels.to_numpy(dtype=int)
    for end in range(SEQUENCE_LENGTH - 1, len(arr)):
        X.append(arr[end - SEQUENCE_LENGTH + 1:end + 1])
        y.append(lab[end])
    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=int)

    split = int(len(X) * 0.8)
    if split <= 0 or split >= len(X):
        raise ValueError("Unable to create train/test evaluation partition.")
    X_test_raw, y_test = X[split:], y[split:]
    n, win, feat = X_test_raw.shape
    X_test_scaled = scaler.transform(X_test_raw.reshape(-1, feat)).reshape(n, win, feat)

    probs = np.asarray(model.predict(X_test_scaled, verbose=0))
    if probs.ndim == 1 or (probs.ndim == 2 and probs.shape[1] == 1):
        fault_probs = probs.reshape(-1)
        y_pred = (fault_probs >= 0.5).astype(int)
    elif probs.ndim == 2 and probs.shape[1] == 2:
        y_pred = np.argmax(probs, axis=1)
        fault_probs = probs[:, 1]
    else:
        raise ValueError(f"Unexpected model output shape: {probs.shape}")

    labels_order = [0, 1]
    cm = confusion_matrix(y_test, y_pred, labels=labels_order)
    metrics = {
        "model": "1D CNN + LSTM",
        "evaluation_type": "provisional held-out 20% of ordered CSV windows",
        "sequence_length": SEQUENCE_LENGTH,
        "features": len(feature_columns),
        "test_samples": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
        "fault_precision": float(precision_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "fault_recall": float(recall_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "fault_f1": float(f1_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "confusion_matrix": {
            "labels": ["Normal (0)", "Fault (1)"],
            "matrix": cm.tolist(),
            "interpretation": {
                "true_normal_pred_normal": int(cm[0,0]),
                "false_alarm_normal_pred_fault": int(cm[0,1]),
                "missed_fault_fault_pred_normal": int(cm[1,0]),
                "detected_fault_fault_pred_fault": int(cm[1,1]),
            },
        },
        "caveat": "CSV has no verified timestamp/asset sequence; verify the original training split and temporal ordering before presenting these metrics as final."
    }
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    report = classification_report(y_test, y_pred, labels=labels_order, target_names=["Normal", "Fault"], zero_division=0)
    (OUTPUT_DIR / "classification_report.txt").write_text(report, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm)
    ax.set_title("CNN + LSTM Confusion Matrix")
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Actual label")
    ax.set_xticks([0,1], ["Normal", "Fault"])
    ax.set_yticks([0,1], ["Normal", "Fault"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i,j]), ha="center", va="center")
    fig.colorbar(im, ax=ax, label="Samples")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "confusion_matrix.png", dpi=160)
    plt.close(fig)
    print(json.dumps(metrics, indent=2))
    print(f"\nSaved metrics: {OUTPUT_DIR / 'metrics.json'}")
    print(f"Saved confusion matrix: {OUTPUT_DIR / 'confusion_matrix.png'}")
    print(f"Saved report: {OUTPUT_DIR / 'classification_report.txt'}")

if __name__ == "__main__":
    main()
