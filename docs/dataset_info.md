# Dataset Information

## Building Data Genome Project 2

This project uses the **Building Data Genome Project 2** dataset for training and demonstration.

**Source:** https://github.com/buds-lab/building-data-genome-project-2

### Dataset Overview

- **1,636 buildings** from various locations worldwide
- **2+ years** of hourly energy meter data
- **Multiple meter types:** electricity, chilled water, steam, hot water
- **Weather data** included for each site

### Data Files

After running `fetch_dataset.py`, the following files are created:

```
data/
├── raw/
│   ├── meters.csv      # Energy readings for all buildings
│   ├── metadata.csv    # Building information
│   └── weather.csv     # Weather data by site
└── processed/
    ├── training_data.csv    # Multi-building data for ML training
    ├── deployment_data.csv  # Single building for demo/monitoring
    └── building_info.json   # Selected building metadata
```

### Training vs Deployment

| Aspect    | Training               | Deployment           |
| --------- | ---------------------- | -------------------- |
| Buildings | 100+ buildings         | 1 building           |
| Purpose   | Train robust ML models | Real-time monitoring |
| Data      | Historical patterns    | Live simulation      |

### Features Used

| Feature     | Description             | Unit |
| ----------- | ----------------------- | ---- |
| energy      | Energy consumption      | kWh  |
| temperature | Outside air temperature | °C   |
| humidity    | Relative humidity       | %    |
| occupancy   | Estimated occupancy     | 0-1  |

### Setup Instructions

1. **Download and prepare dataset:**

   ```bash
   cd digital_twin_smart_buildings
   python scripts/fetch_dataset.py
   ```

2. **Train anomaly detection models:**

   ```bash
   python scripts/train_anomaly.py
   ```

3. **Train forecasting models:**

   ```bash
   python scripts/train_forecasting.py
   ```

4. **Start the backend:**
   ```bash
   cd backend
   python main.py
   ```

### Citation

If using this dataset for research:

```
@article{miller2020building,
  title={The Building Data Genome Project 2},
  author={Miller, Clayton and others},
  journal={Scientific Data},
  year={2020}
}
```
