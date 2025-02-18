# app/scheduler.py
from flask_apscheduler import APScheduler
from .helpers import delete_inactive_sites

scheduler = APScheduler()


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(
        id="delete_job",
        func=delete_inactive_sites,
        trigger="interval",
        days=1,
    )
