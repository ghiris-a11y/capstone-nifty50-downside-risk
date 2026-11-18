"""Smoke tests for the project scaffold (P0)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "config", "data/raw", "data/frozen", "data/live", "data/processed", "data/logs",
    "src", "frontend", ".github/workflows",
    "outputs/tables", "outputs/figures", "outputs/models", "outputs/live",
    "report/template", "report/chapters", "report/figures", "tests",
]


def test_folder_layout_exists():
    missing = [d for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
    assert not missing, f"Missing folders: {missing}"


def test_requirements_are_pinned():
    lines = [
        ln.strip() for ln in (ROOT / "requirements.txt").read_text().splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    assert lines, "requirements.txt is empty"
    unpinned = [ln for ln in lines if "==" not in ln]
    assert not unpinned, f"Unpinned packages: {unpinned}"


def test_core_packages_import():
    import arch, numpy, pandas, scipy, sklearn, xgboost  # noqa: F401
