"""
Train energy forecasting models on Building Data Genome Project 2 dataset.

Models trained:
1. LSTM for energy forecasting
2. LSTM for occupancy prediction (based on patterns)
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "backend" / "models" / "forecasting"

# Forecasting parameters
SEQUENCE_LENGTH = 24  # Use 24 hours of history
FORECAST_HORIZON = 24  # Predict next 24 hours


def load_deployment_data() -> pd.DataFrame:
    """Load the processed deployment data (single building)."""
    data_path = DATA_DIR / "deployment_data.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"Deployment data not found at {data_path}. "
            "Run 'python scripts/fetch_dataset.py' first."
        )
    
    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    print(f"Loaded deployment data: {df.shape}")
    return df


def create_sequences(
    data: np.ndarray,
    seq_length: int,
    horizon: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Create sequences for time series forecasting.
    
    Args:
        data: Input array of shape (n_samples, n_features)
        seq_length: Number of past time steps to use
        horizon: Number of future steps to predict
    
    Returns:
        X: Input sequences (n_sequences, seq_length, n_features)
        y: Target values (n_sequences, horizon)
    """
    X, y = [], []
    
    for i in range(len(data) - seq_length - horizon + 1):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length:i + seq_length + horizon, 0])  # Predict first feature
    
    return np.array(X), np.array(y)


def build_lstm_model(
    seq_length: int,
    n_features: int,
    horizon: int
) -> keras.Model:
    """
    Build LSTM model for time series forecasting.
    """
    model = keras.Sequential([
        layers.LSTM(64, return_sequences=True, input_shape=(seq_length, n_features)),
        layers.Dropout(0.2),
        layers.LSTM(32, return_sequences=False),
        layers.Dropout(0.2),
        layers.Dense(32, activation="relu"),
        layers.Dense(horizon)
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="mse",
        metrics=["mae"]
    )
    
    return model


def train_energy_forecaster(df: pd.DataFrame) -> tuple[keras.Model, MinMaxScaler]:
    """
    Train LSTM model for energy forecasting.
    """
    print("\n" + "=" * 50)
    print("Training Energy Forecasting Model...")
    print("=" * 50)
    
    # Prepare features
    features = ["energy", "temperature", "humidity"]
    data = df[features].values
    
    # Scale data
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)
    
    # Create sequences
    X, y = create_sequences(data_scaled, SEQUENCE_LENGTH, FORECAST_HORIZON)
    print(f"  Input shape: {X.shape}")
    print(f"  Output shape: {y.shape}")
    
    # Split data
    train_size = int(len(X) * 0.8)
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    
    # Build and train model
    model = build_lstm_model(SEQUENCE_LENGTH, len(features), FORECAST_HORIZON)
    model.summary()
    
    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=10,
        restore_best_weights=True
    )
    
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=[early_stop],
        verbose=1
    )
    
    print(f"\n  Final training loss: {history.history['loss'][-1]:.6f}")
    print(f"  Final validation loss: {history.history['val_loss'][-1]:.6f}")
    
    return model, scaler


def train_occupancy_predictor(df: pd.DataFrame) -> tuple[keras.Model, MinMaxScaler]:
    """
    Train LSTM model for occupancy prediction.
    """
    print("\n" + "=" * 50)
    print("Training Occupancy Prediction Model...")
    print("=" * 50)
    
    # Add time features
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["dayofweek"] = df["timestamp"].dt.dayofweek
    
    # Cyclical encoding
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
    
    # Features for occupancy prediction
    features = ["occupancy", "hour_sin", "hour_cos", "dow_sin", "dow_cos", "energy"]
    data = df[features].values
    
    # Scale data
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)
    
    # Create sequences (shorter for occupancy)
    seq_len = 12  # 12 hours history
    horizon = 12  # Predict 12 hours ahead
    
    X, y = create_sequences(data_scaled, seq_len, horizon)
    print(f"  Input shape: {X.shape}")
    print(f"  Output shape: {y.shape}")
    
    # Split data
    train_size = int(len(X) * 0.8)
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    
    # Build and train model
    model = build_lstm_model(seq_len, len(features), horizon)
    
    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=10,
        restore_best_weights=True
    )
    
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=[early_stop],
        verbose=1
    )
    
    print(f"\n  Final training loss: {history.history['loss'][-1]:.6f}")
    print(f"  Final validation loss: {history.history['val_loss'][-1]:.6f}")
    
    return model, scaler


def save_models(
    energy_model: keras.Model,
    energy_scaler: MinMaxScaler,
    occupancy_model: keras.Model,
    occupancy_scaler: MinMaxScaler
) -> None:
    """Save trained models to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save energy forecasting model
    energy_model.save(MODEL_DIR / "lstm_energy.h5")
    joblib.dump(energy_scaler, MODEL_DIR / "lstm_energy_scaler.pkl")
    print(f"\nSaved energy model: {MODEL_DIR / 'lstm_energy.h5'}")
    
    # Save occupancy prediction model
    occupancy_model.save(MODEL_DIR / "lstm_occupancy.h5")
    joblib.dump(occupancy_scaler, MODEL_DIR / "lstm_occupancy_scaler.pkl")
    print(f"Saved occupancy model: {MODEL_DIR / 'lstm_occupancy.h5'}")
    
    # Note: The original .pkl files were placeholders
    # We're now using .h5 for Keras models


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("Forecasting Model Training")
    print("=" * 60)
    
    # Load data
    df = load_deployment_data()
    
    # Train energy forecasting model
    energy_model, energy_scaler = train_energy_forecaster(df)
    
    # Train occupancy prediction model
    occupancy_model, occupancy_scaler = train_occupancy_predictor(df)
    
    # Save models
    save_models(energy_model, energy_scaler, occupancy_model, occupancy_scaler)
    
    print("\n" + "=" * 60)
    print("Forecasting model training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

