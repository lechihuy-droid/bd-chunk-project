from domain.manifest import manifest_hash


def test_manifest_hash_is_order_independent_and_input_sensitive() -> None:
    components = [
        {"kind": "PROMPT", "ref": "mlflow://prompt", "exact_version": "1", "extra": {}},
        {"kind": "MODEL", "ref": "model://model", "exact_version": "model", "extra": {}},
    ]
    first = manifest_hash(
        release_id="release",
        git_commit="a" * 40,
        model_profile="model",
        runtime_adapter_id="langgraph",
        input_hash="sha256:" + "b" * 64,
        components=components,
    )
    second = manifest_hash(
        release_id="release",
        git_commit="a" * 40,
        model_profile="model",
        runtime_adapter_id="langgraph",
        input_hash="sha256:" + "b" * 64,
        components=list(reversed(components)),
    )
    changed_input = manifest_hash(
        release_id="release",
        git_commit="a" * 40,
        model_profile="model",
        runtime_adapter_id="langgraph",
        input_hash="sha256:" + "c" * 64,
        components=components,
    )
    assert first == second
    assert first != changed_input
