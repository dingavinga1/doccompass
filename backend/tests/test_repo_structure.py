from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def test_backend_directories_exist():
    expected = [
        BACKEND / "app" / "api",
        BACKEND / "app" / "models",
        BACKEND / "app" / "services",
        BACKEND / "app" / "tasks",
        BACKEND / "app" / "mcp",
        BACKEND / "tests",
    ]
    for path in expected:
        assert path.exists(), f"Missing expected path: {path}"


def test_frontend_directories_exist():
    expected = [
        FRONTEND / "src" / "pages",
        FRONTEND / "src" / "components",
        FRONTEND / "src" / "api",
        FRONTEND / "tests",
    ]
    for path in expected:
        assert path.exists(), f"Missing expected path: {path}"


def test_makefile_targets_present():
    makefile = ROOT / "Makefile"
    text = makefile.read_text(encoding="utf-8")

    for target in ["bootstrap:", "test-backend:", "run-backend:", "up:", "down:", "ps:"]:
        assert target in text, f"Target not found: {target}"
