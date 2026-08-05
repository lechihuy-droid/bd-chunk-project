from fastapi import APIRouter, Response, status
import boto3
import httpx
from sqlalchemy import text

from config import load_settings
from persistence.session import get_engine

router = APIRouter()


# Hai đường tới cùng một handler, cố ý:
#   /health          — docker healthcheck gọi từ trong container, giữ ngắn gọn
#   /api/vgov/health — đường đi qua Hub proxy; proxy luôn giữ nguyên prefix /api/vgov
# Thiếu đường thứ hai thì `curl localhost:8799/api/vgov/health` trả 404 khi stack đang chạy và 502
# khi stack tắt — tức smoke test health qua Hub chỉ đúng ở nhánh "stack tắt".
@router.get("/health")
@router.get("/api/vgov/health")
async def health(response: Response) -> dict[str, object]:
    settings = load_settings()
    dependencies: dict[str, str] = {}

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        dependencies["postgres"] = "ok"
    except Exception:
        dependencies["postgres"] = "error"

    try:
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
        client.list_buckets()
        dependencies["minio"] = "ok"
    except Exception:
        dependencies["minio"] = "error"

    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in {
            "mlflow": settings.mlflow_tracking_uri,
            "runtime": settings.runtime_base_url,
        }.items():
            try:
                result = await client.get(f"{url}/health")
                dependencies[name] = "ok" if result.is_success else "error"
            except httpx.HTTPError:
                dependencies[name] = "error"

    is_healthy = all(value == "ok" for value in dependencies.values())
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if is_healthy else "error", "dependencies": dependencies}
