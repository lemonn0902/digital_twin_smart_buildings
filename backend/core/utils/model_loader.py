from pathlib import Path
from typing import Any


BASE_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def get_model_path(*relative_parts: str) -> Path:
    """
    Convenience helper to reference model artifact files.
    """
    return BASE_MODELS_DIR.joinpath(*relative_parts)


def load_stub_model(name: str) -> Any:
    """
    For now, just return the model name.
    Later you can implement real loading logic with joblib / keras / etc.
    """
    return {"model_name": name}
