from .celery_app import celery_app


@celery_app.task(name="app.tasks.ping")
def ping() -> str:
    return "pong"
