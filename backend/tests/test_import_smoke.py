import importlib


MODULES = [
    "app.main",
    "app.config",
    "app.db",
    "app.redis_client",
    "app.celery_app",
    "app.tasks.ping",
    "app.api",
    "app.api.documentation",
    "app.api.dtos.documentation",
    "app.models",
    "app.services",
    "app.services.documentation",
    "app.mcp",
]


def test_core_modules_importable():
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        assert module is not None
