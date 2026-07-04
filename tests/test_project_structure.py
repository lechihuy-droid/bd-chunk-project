from pathlib import Path


def test_harness_structure_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / "harness").exists()
    assert (root / "ontology").exists()
    assert (root / "src" / "bd_chunk").exists()
