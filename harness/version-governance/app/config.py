from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str
    mlflow_tracking_uri: str
    runtime_base_url: str
    callback_base_url: str
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    git_repo_path: str
    nvidia_api_key: str | None
    base_url: str
    callback_grace_seconds: int


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        database_url=_required("VGOV_DATABASE_URL"),
        mlflow_tracking_uri=_required("VGOV_MLFLOW_TRACKING_URI"),
        runtime_base_url=_required("VGOV_RUNTIME_BASE_URL"),
        callback_base_url=_required("VGOV_CALLBACK_BASE_URL"),
        s3_endpoint=_required("VGOV_S3_ENDPOINT"),
        s3_access_key=_required("VGOV_S3_ACCESS_KEY"),
        s3_secret_key=_required("VGOV_S3_SECRET_KEY"),
        git_repo_path=_required("VGOV_GIT_REPO_PATH"),
        nvidia_api_key=os.getenv("NVIDIA_API_KEY"),
        base_url=_required("VGOV_BASE_URL"),
        callback_grace_seconds=int(os.getenv("VGOV_CALLBACK_GRACE_SECONDS", "120")),
    )
