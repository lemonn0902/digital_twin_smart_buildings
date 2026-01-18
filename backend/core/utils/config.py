from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Core metadata
    project_name: str = "Digital Twin Smart Building"
    environment: str = "development"
    api_version: str = "0.1.0"

    # Database - defaults to SQLite for easy development
    # Override with DB_URL environment variable for PostgreSQL
    db_url: str = "sqlite:///./digital_twin.db"
    
    # InfluxDB (for time-series data) - optional for now
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = ""
    influxdb_org: str = "digital-twin"
    influxdb_bucket: str = "building_telemetry"
    influxdb_verify_ssl: bool = True
    
    # Neo4j (for graph-based layout)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Model paths
    models_dir: Path = PROJECT_ROOT / "backend" / "models"
    
    # API settings
    api_base_url: str = "http://localhost:8000"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # WebSocket settings
    websocket_heartbeat_interval: int = 30  # seconds
    
    # Simulation defaults
    default_simulation_resolution_minutes: int = 15
    default_simulation_horizon_hours: int = 24

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
