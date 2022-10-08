from celery import Celery

from .app import app

worker = Celery(app.name, broker="redis://127.0.0.1:6379/0")
worker.conf.update(app.config)
