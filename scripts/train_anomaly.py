"""
Train anomaly detection models on Building Data Genome Project 2 dataset.

Models trained:
1. Isolation Forest - for unsupervised anomaly detection
2. Autoencoder - for reconstruction-based anomaly detection
"""

import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# TensorFlow imports
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "backend" / "models" / "anomaly"


def load_training_data() -> pd.DataFrame:
    """Load the processed training data."""
    data_path = DATA_DIR / "training_data.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"Training data not found at {data_path}. "
            "Run 'python scripts/fetch_dataset.py' first."
        )
    
    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    print(f"Loaded training data: {df.shape}")
    return df


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    """
    Prepare features for anomaly detection.
    
    Features:
    - energy: Energy consumption
    - temperature: Outside temperature
    - humidity: Relative humidity
    - hour: Hour of day (cyclical)
    - dayofweek: Day of week (cyclical)
    """
    # Add time features
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["dayofweek"] = df["timestamp"].dt.dayofweek
    
    # Cyclical encoding for time features
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
    
    # Select features
    feature_cols = ["energy", "temperature", "humidity", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    X = df[feature_cols].values
    
    # Handle any remaining NaN values
    X = np.nan_to_num(X, nan=0.0)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, scaler


def train_isolation_forest(X: np.ndarray) -> IsolationForest:
    """
    Train Isolation Forest model.
    
    Isolation Forest isolates anomalies by randomly selecting features
    and split values. Anomalies require fewer splits to isolate.
    """
    print("\n" + "=" * 50)
    print("Training Isolation Forest...")
    print("=" * 50)
    
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,  # Expect ~5% anomalies
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    model.fit(X)
    
    # Get anomaly scores for evaluation
    scores = model.score_samples(X)
    threshold = np.percentile(scores, 5)
    
    print(f"  Trained on {X.shape[0]} samples")
    print(f"  Anomaly score threshold (5th percentile): {threshold:.4f}")
    
    return model


def build_autoencoder(input_dim: int) -> keras.Model:
    """
    Build autoencoder model for anomaly detection.
    
    The autoencoder learns to compress and reconstruct normal data.
    Anomalies will have higher reconstruction error.
    """
    # Encoder
    inputs = keras.Input(shape=(input_dim,))
    x = layers.Dense(32, activation="relu")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(16, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    encoded = layers.Dense(8, activation="relu")(x)
    
    # Decoder
    x = layers.Dense(16, activation="relu")(encoded)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(32, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    decoded = layers.Dense(input_dim, activation="linear")(x)
    
    model = keras.Model(inputs, decoded, name="autoencoder")
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="mse"
    )
    
    return model


def train_autoencoder(X: np.ndarray) -> keras.Model:
    """Train autoencoder model."""
    print("\n" + "=" * 50)
    print("Training Autoencoder...")
    print("=" * 50)
    
    input_dim = X.shape[1]
    model = build_autoencoder(input_dim)
    
    model.summary()
    
    # Early stopping to prevent overfitting
    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    )
    
    # Train
    history = model.fit(
        X, X,  # Autoencoder reconstructs input
        epochs=50,
        batch_size=256,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=1
    )
    
    # Calculate reconstruction error threshold
    reconstructions = model.predict(X, verbose=0)
    mse = np.mean(np.square(X - reconstructions), axis=1)
    threshold = np.percentile(mse, 95)
    
    print(f"\n  Final training loss: {history.history['loss'][-1]:.6f}")
    print(f"  Final validation loss: {history.history['val_loss'][-1]:.6f}")
    print(f"  Reconstruction error threshold (95th percentile): {threshold:.6f}")
    
    return model


def save_models(
    isolation_forest: IsolationForest,
    autoencoder: keras.Model,
    scaler: StandardScaler
) -> None:
    """Save trained models to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save Isolation Forest
    if_path = MODEL_DIR / "isolation_forest.pkl"
    joblib.dump(isolation_forest, if_path)
    print(f"\nSaved Isolation Forest: {if_path}")
    
    # Save Autoencoder
    ae_path = MODEL_DIR / "autoencoder.h5"
    autoencoder.save(ae_path)
    print(f"Saved Autoencoder: {ae_path}")
    
    # Save scaler for inference
    scaler_path = MODEL_DIR / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"Saved Scaler: {scaler_path}")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("Anomaly Detection Model Training")
    print("=" * 60)
    
    # Load data
    df = load_training_data()
    
    # Prepare features
    X, scaler = prepare_features(df)
    print(f"\nFeature matrix shape: {X.shape}")
    
    # Train Isolation Forest
    isolation_forest = train_isolation_forest(X)
    
    # Train Autoencoder
    autoencoder = train_autoencoder(X)
    
    # Save models
    save_models(isolation_forest, autoencoder, scaler)
    
    print("\n" + "=" * 60)
    print("Anomaly detection training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

