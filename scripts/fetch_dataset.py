"""
Prepare ASHRAE Energy Prediction Dataset for digital twin.
https://www.kaggle.com/c/ashrae-energy-prediction/data

Download Instructions:
1. Go to https://www.kaggle.com/c/ashrae-energy-prediction/data
2. Download: train.csv, building_metadata.csv, weather_train.csv
3. Place them in: digital_twin_smart_buildings/data/raw/

Training uses multiple buildings; deployment focuses on one building.
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
import json

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def check_dataset_exists() -> bool:
    """Check if ASHRAE dataset files exist."""
    required_files = ["train.csv", "building_metadata.csv", "weather_train.csv"]
    
    for f in required_files:
        if not (RAW_DIR / f).exists():
            return False
    return True


def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load ASHRAE dataset files."""
    print("\nLoading raw data...")
    
    # Load meter readings
    print("  Loading train.csv (this may take a moment)...")
    train = pd.read_csv(RAW_DIR / "train.csv")
    train["timestamp"] = pd.to_datetime(train["timestamp"])
    print(f"    Train: {train.shape}")
    
    # Load building metadata
    metadata = pd.read_csv(RAW_DIR / "building_metadata.csv")
    print(f"    Metadata: {metadata.shape}")
    
    # Load weather data
    weather = pd.read_csv(RAW_DIR / "weather_train.csv")
    weather["timestamp"] = pd.to_datetime(weather["timestamp"])
    print(f"    Weather: {weather.shape}")
    
    return train, metadata, weather


def select_building(metadata: pd.DataFrame, primary_use: str = "Office") -> int:
    """Select a representative building for deployment."""
    # Filter by primary use
    candidates = metadata[metadata["primary_use"] == primary_use]
    
    if candidates.empty:
        # Fallback to Education
        candidates = metadata[metadata["primary_use"] == "Education"]
    
    if candidates.empty:
        candidates = metadata.head(10)
    
    # Pick first candidate
    selected = candidates.iloc[0]["building_id"]
    print(f"\nSelected building for deployment: {selected} ({primary_use})")
    return int(selected)


def prepare_training_data(
    train: pd.DataFrame,
    metadata: pd.DataFrame,
    weather: pd.DataFrame,
    sample_buildings: int = 100,
    meter_type: int = 0  # 0 = electricity
) -> pd.DataFrame:
    """
    Prepare training data from multiple buildings.
    
    Args:
        train: Meter readings
        metadata: Building info
        weather: Weather data
        sample_buildings: Number of buildings to use
        meter_type: 0=electricity, 1=chilled water, 2=steam, 3=hot water
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nPreparing training data...")
    print(f"  Using meter type: {meter_type} (electricity)")
    
    # Filter to electricity meters only
    train_elec = train[train["meter"] == meter_type].copy()
    
    # Get unique buildings with electricity data
    buildings_with_data = train_elec["building_id"].unique()
    selected_buildings = buildings_with_data[:sample_buildings]
    
    print(f"  Selected {len(selected_buildings)} buildings for training")
    
    # Filter to selected buildings
    train_subset = train_elec[train_elec["building_id"].isin(selected_buildings)]
    
    # Merge with metadata to get site_id
    train_subset = train_subset.merge(
        metadata[["building_id", "site_id", "primary_use", "square_feet"]],
        on="building_id",
        how="left"
    )
    
    # Merge with weather
    train_subset = train_subset.merge(
        weather[["site_id", "timestamp", "air_temperature", "dew_temperature", 
                 "sea_level_pressure", "wind_speed"]],
        on=["site_id", "timestamp"],
        how="left"
    )
    
    # Rename columns
    # Note: We map dew_temperature -> humidity so it matches the expectations
    # in the anomaly training pipeline (`train_anomaly.py`).
    train_subset = train_subset.rename(columns={
        "meter_reading": "energy",
        "air_temperature": "temperature",
        "dew_temperature": "humidity"  # Using dew temp as humidity proxy
    })
    
    # Drop rows with missing values
    train_subset = train_subset.dropna(subset=["energy", "temperature"])
    
    # Save training data
    output_path = PROCESSED_DIR / "training_data.csv"
    train_subset.to_csv(output_path, index=False)
    print(f"  Training data saved: {output_path}")
    print(f"  Shape: {train_subset.shape}")
    
    return train_subset


def prepare_deployment_data(
    train: pd.DataFrame,
    metadata: pd.DataFrame,
    weather: pd.DataFrame,
    building_id: int,
    meter_type: int = 0
) -> pd.DataFrame:
    """
    Prepare data for a single building (deployment/demo).
    """
    print(f"\nPreparing deployment data for building: {building_id}...")
    
    # Filter to this building and electricity meter
    building_data = train[
        (train["building_id"] == building_id) & 
        (train["meter"] == meter_type)
    ].copy()
    
    if building_data.empty:
        raise ValueError(f"No data found for building {building_id}")
    
    # Get site_id
    site_id = metadata[metadata["building_id"] == building_id]["site_id"].values[0]
    
    # Merge with weather
    site_weather = weather[weather["site_id"] == site_id].copy()
    
    building_data = building_data.merge(
        site_weather[["timestamp", "air_temperature", "dew_temperature", "wind_speed"]],
        on="timestamp",
        how="left"
    )
    
    # Rename columns
    building_data = building_data.rename(columns={
        "meter_reading": "energy",
        "air_temperature": "temperature",
        "dew_temperature": "humidity"
    })
    
    # Add simulated occupancy based on time patterns
    building_data["hour"] = building_data["timestamp"].dt.hour
    building_data["dayofweek"] = building_data["timestamp"].dt.dayofweek
    
    def estimate_occupancy(row):
        if row["dayofweek"] >= 5:  # Weekend
            return 0.1 + np.random.normal(0, 0.05)
        hour = row["hour"]
        if 9 <= hour <= 17:  # Business hours
            return 0.7 + 0.2 * (1 - abs(hour - 13) / 4) + np.random.normal(0, 0.05)
        elif 7 <= hour <= 9 or 17 <= hour <= 19:  # Transition
            return 0.4 + np.random.normal(0, 0.05)
        else:
            return 0.05 + np.random.normal(0, 0.02)
    
    building_data["occupancy"] = building_data.apply(estimate_occupancy, axis=1)
    building_data["occupancy"] = building_data["occupancy"].clip(0, 1)
    
    # Select final columns
    building_data = building_data[[
        "timestamp", "energy", "temperature", "humidity", "occupancy"
    ]].dropna()
    
    building_data = building_data.sort_values("timestamp").reset_index(drop=True)
    
    # Save deployment data
    output_path = PROCESSED_DIR / "deployment_data.csv"
    building_data.to_csv(output_path, index=False)
    print(f"  Deployment data saved: {output_path}")
    print(f"  Shape: {building_data.shape}")
    print(f"  Date range: {building_data['timestamp'].min()} to {building_data['timestamp'].max()}")
    
    # Save building info
    building_info = metadata[metadata["building_id"] == building_id].to_dict(orient="records")[0]
    building_info["building_id"] = int(building_info["building_id"])
    building_info["site_id"] = int(building_info["site_id"])
    
    info_path = PROCESSED_DIR / "building_info.json"
    with open(info_path, "w") as f:
        json.dump(building_info, f, indent=2, default=str)
    print(f"  Building info saved: {info_path}")
    
    return building_data


def print_download_instructions():
    """Print instructions for downloading the dataset."""
    print("\n" + "=" * 60)
    print("ASHRAE Dataset Not Found!")
    print("=" * 60)
    print("\nPlease download the dataset from Kaggle:")
    print("  https://www.kaggle.com/c/ashrae-energy-prediction/data")
    print("\nRequired files:")
    print("  - train.csv")
    print("  - building_metadata.csv")
    print("  - weather_train.csv")
    print(f"\nPlace them in: {RAW_DIR}")
    print("\nAlternatively, use Kaggle CLI:")
    print("  pip install kaggle")
    print("  kaggle competitions download -c ashrae-energy-prediction")
    print("  unzip ashrae-energy-prediction.zip -d data/raw/")
    print("=" * 60)


def main():
    """Main function to prepare dataset."""
    print("=" * 60)
    print("ASHRAE Energy Prediction Dataset - Preparation")
    print("=" * 60)
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if dataset exists
    if not check_dataset_exists():
        print_download_instructions()
        return
    
    # Load raw data
    train, metadata, weather = load_raw_data()
    
    # Select a building for deployment
    building_id = select_building(metadata, "Office")
    
    # Prepare training data (multiple buildings)
    prepare_training_data(train, metadata, weather, sample_buildings=100)
    
    # Prepare deployment data (single building)
    prepare_deployment_data(train, metadata, weather, building_id)
    
    print("\n" + "=" * 60)
    print("Dataset preparation complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python scripts/train_anomaly.py")
    print("2. Run: python scripts/train_forecasting.py")
    print("3. Start the backend: cd backend && python main.py")


if __name__ == "__main__":
    main()
