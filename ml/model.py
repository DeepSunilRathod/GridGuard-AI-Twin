
import tensorflow as tf
from tensorflow.keras import layers, models


def build_cnn_lstm(input_shape, num_classes=2):
    """
    Experimental 1D CNN + LSTM classifier.

    input_shape: (sequence_length, number_of_features)

    Note: the model learns temporal patterns only if the input
    sequences genuinely represent ordered observations. For the
    current dataset, that assumption has not been verified.
    """
    inputs = layers.Input(shape=input_shape, name="sensor_sequence")

    x = layers.Conv1D(
        filters=32,
        kernel_size=3,
        padding="same",
        activation="relu",
    )(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=2, padding="same")(x)

    x = layers.Conv1D(
        filters=64,
        kernel_size=3,
        padding="same",
        activation="relu",
    )(x)
    x = layers.Dropout(0.2)(x)

    x = layers.LSTM(32, return_sequences=False)(x)
    x = layers.Dense(32, activation="relu")(x)
    x = layers.Dropout(0.3)(x)

    outputs = layers.Dense(
        num_classes,
        activation="softmax",
        name="fault_probabilities",
    )(x)

    model = models.Model(inputs, outputs, name="GridGuard_CNN_LSTM")

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model

