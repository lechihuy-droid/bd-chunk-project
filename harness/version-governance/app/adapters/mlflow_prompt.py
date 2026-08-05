import mlflow.genai  # noqa: F401  - nạp namespace genai để MlflowClient có API prompt
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

from ports.prompt_registry import PromptResolutionError, ResolvedPrompt


class MlflowPromptAdapter:
    """Resolve alias/version thành exact immutable prompt version.

    Dùng `MlflowClient`, KHÔNG dùng `mlflow.genai.load_prompt`. `load_prompt` cache kết quả trong
    process: sau khi một process khác di chuyển alias, process này vẫn trả version cũ. Đã đo thật
    trên MLflow 3.15 — flip alias 1->2 từ process ngoài rồi đọc lại:

        mlflow.genai.load_prompt(...)                 -> 1   (stale)
        MlflowClient().get_prompt_version_by_alias(..) -> 2   (đúng)

    vgov-api là process sống lâu, nên nếu dùng `load_prompt` thì Frozen Run Manifest sẽ ghi prompt
    version SAI — phá FR-MAN-001 và DoD #3.
    """

    def __init__(self, client: MlflowClient | None = None) -> None:
        self._client = client

    def resolve(
        self,
        name: str,
        *,
        alias: str | None = None,
        version: int | None = None,
    ) -> ResolvedPrompt:
        if (alias is None) == (version is None):
            raise PromptResolutionError("Provide exactly one of alias or version")

        client = self._client or MlflowClient()
        try:
            if alias is not None:
                prompt = client.get_prompt_version_by_alias(name, alias)
            else:
                prompt = client.get_prompt_version(name, str(version))
        except MlflowException as exc:
            raise PromptResolutionError(str(exc)) from exc

        if prompt is None:
            raise PromptResolutionError(f"Prompt not found: {name} alias={alias} version={version}")

        exact_version = int(prompt.version)
        return ResolvedPrompt(
            registry="mlflow",
            name=prompt.name,
            version=exact_version,
            template=prompt.template,
            uri=f"prompts:/{prompt.name}/{exact_version}",
        )
