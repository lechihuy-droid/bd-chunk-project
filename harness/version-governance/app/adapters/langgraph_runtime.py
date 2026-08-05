import httpx

from ports.runtime import (
    CancelRunRequest,
    ResumeRunRequest,
    RuntimeCapabilityNotSupported,
    RuntimeHandle,
    RuntimeStatus,
    StartRunRequest,
)


class LangGraphRuntimeAdapter:
    # httpx mặc định 5s. Runtime phải nạp MLflow experiment trước khi trả handle nên lần gọi đầu
    # vượt 5s -> start() ném ReadTimeout, run bị đánh FAILED trong khi runtime vẫn chạy tiếp và
    # callback về sau ghi đè thành SUCCEEDED. Đặt timeout tường minh để không có cửa sổ đó.
    START_TIMEOUT_SECONDS = 60.0
    STATUS_TIMEOUT_SECONDS = 10.0

    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def start(self, req: StartRunRequest) -> RuntimeHandle:
        async with self._client(self.START_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}/runs",
                json={**req.__dict__, "prompts": [prompt.__dict__ for prompt in req.prompts]},
            )
            response.raise_for_status()
            data = response.json()

        status = data["status"]
        return RuntimeHandle(
            provider=data["provider"],
            runtime_run_id=data["runtime_run_id"],
            runtime_thread_id=data.get("runtime_thread_id"),
            status=RuntimeStatus(
                canonical=status["canonical"],
                provider_status=status["provider_status"],
                detail=status.get("detail"),
            ),
        )

    async def get_status(self, runtime_run_id: str) -> RuntimeStatus:
        async with self._client(self.STATUS_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{self.base_url}/runs/{runtime_run_id}")
            response.raise_for_status()
            data = response.json()

        raw_status = str(data.get("canonical", data.get("provider_status", ""))).strip().lower()
        mapping = {
            "pending": "PENDING",
            "queued": "PENDING",
            "running": "RUNNING",
            "success": "SUCCEEDED",
            "succeeded": "SUCCEEDED",
            "error": "FAILED",
            "failed": "FAILED",
            "timeout": "FAILED",
            "cancelled": "CANCELLED",
        }
        canonical = mapping.get(raw_status)
        if canonical is None:
            return RuntimeStatus(
                canonical="FAILED",
                provider_status=data.get("provider_status", "unknown"),
                detail="RUNTIME_STATUS_UNKNOWN",
            )
        return RuntimeStatus(
            canonical=canonical,
            provider_status=data.get("provider_status", "unknown"),
            detail=data.get("detail"),
        )

    async def resume(self, req: ResumeRunRequest) -> RuntimeHandle:
        raise RuntimeCapabilityNotSupported()

    async def cancel(self, req: CancelRunRequest) -> RuntimeHandle:
        raise RuntimeCapabilityNotSupported()

    def _client(self, timeout_seconds: float):
        if self.client is not None:
            return _NoClose(self.client)
        return httpx.AsyncClient(timeout=timeout_seconds)


class _NoClose:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self.client

    async def __aexit__(self, *args: object) -> bool:
        return False
