"""
Data service for loading and serving building data.
Uses the processed Building Data Genome Project 2 dataset.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

import pandas as pd
import numpy as np

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"


class DataService:
    """Service for managing building data from the dataset."""
    
    _instance = None
    _data: Optional[pd.DataFrame] = None
    _building_info: Optional[Dict] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _load_data(self) -> None:
        """Load deployment data if not already loaded."""
        if self._data is not None:
            return
        
        data_path = DATA_DIR / "deployment_data.csv"
        
        if data_path.exists():
            self._data = pd.read_csv(data_path, parse_dates=["timestamp"])
            self._data = self._data.sort_values("timestamp").reset_index(drop=True)
            print(f"Loaded deployment data: {self._data.shape}")
        else:
            # Generate synthetic data as fallback
            print("Warning: No deployment data found. Using synthetic data.")
            self._data = self._generate_synthetic_data()
        
        # Load building info
        info_path = DATA_DIR / "building_info.json"
        if info_path.exists():
            with open(info_path) as f:
                self._building_info = json.load(f)
    
    def _generate_synthetic_data(self) -> pd.DataFrame:
        """Generate synthetic data as fallback."""
        dates = pd.date_range(
            start="2023-01-01",
            end="2023-12-31",
            freq="H"
        )
        
        n = len(dates)
        hours = dates.hour
        days = dates.dayofweek
        
        # Synthetic patterns
        base_energy = 100
        hourly_pattern = 20 * np.sin(2 * np.pi * hours / 24 - np.pi/2)
        weekly_pattern = 10 * (days < 5).astype(float)
        noise = np.random.normal(0, 5, n)
        
        energy = base_energy + hourly_pattern + weekly_pattern + noise
        energy = np.maximum(energy, 10)  # Minimum energy
        
        temperature = 20 + 10 * np.sin(2 * np.pi * np.arange(n) / (24 * 365)) + np.random.normal(0, 2, n)
        humidity = 50 + 20 * np.sin(2 * np.pi * np.arange(n) / (24 * 30)) + np.random.normal(0, 5, n)
        
        # Occupancy
        occupancy = np.where(
            (hours >= 9) & (hours <= 17) & (days < 5),
            0.7 + np.random.normal(0, 0.1, n),
            0.1 + np.random.normal(0, 0.05, n)
        )
        occupancy = np.clip(occupancy, 0, 1)
        
        return pd.DataFrame({
            "timestamp": dates,
            "energy": energy,
            "temperature": temperature,
            "humidity": np.clip(humidity, 0, 100),
            "occupancy": occupancy
        })
    
    def get_data(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get building data for a time range.
        
        Args:
            start_time: Start of time range (default: 7 days ago)
            end_time: End of time range (default: now)
            metrics: List of metrics to return (default: all)
        
        Returns:
            DataFrame with requested data
        """
        self._load_data()
        
        df = self._data.copy()
        
        # Filter by time
        if start_time:
            df = df[df["timestamp"] >= start_time]
        if end_time:
            df = df[df["timestamp"] <= end_time]
        
        # Filter by metrics
        if metrics:
            cols = ["timestamp"] + [m for m in metrics if m in df.columns]
            df = df[cols]
        
        return df
    
    def get_latest(self, n_hours: int = 24) -> pd.DataFrame:
        """Get the latest n hours of data."""
        self._load_data()
        
        # Use the last n_hours from the dataset
        # (simulating "current" data from historical dataset)
        return self._data.tail(n_hours).copy()
    
    def get_building_info(self) -> Dict:
        """Get building metadata."""
        self._load_data()
        
        if self._building_info:
            return self._building_info
        
        return {
            "building_id": "demo_building",
            "name": "Demo Building",
            "type": "Office",
            "sqft": 50000,
            "floors": 3,
            "year_built": 2010
        }
    
    def get_statistics(self) -> Dict:
        """Get summary statistics for the building."""
        self._load_data()
        
        df = self._data
        
        return {
            "total_records": len(df),
            "date_range": {
                "start": df["timestamp"].min().isoformat(),
                "end": df["timestamp"].max().isoformat()
            },
            "energy": {
                "mean": float(df["energy"].mean()),
                "min": float(df["energy"].min()),
                "max": float(df["energy"].max()),
                "std": float(df["energy"].std())
            },
            "temperature": {
                "mean": float(df["temperature"].mean()),
                "min": float(df["temperature"].min()),
                "max": float(df["temperature"].max())
            },
            "occupancy": {
                "mean": float(df["occupancy"].mean()),
                "peak_hours": "9:00 - 17:00"
            }
        }


# Singleton instance
data_service = DataService()

