from flask import current_app
from datetime import datetime, timedelta
import os
import shutil


def delete_inactive_sites():
    from .models import db, Site  # lazy import to avoid circular dependency

    with current_app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=30)
        sites = Site.query.filter(Site.last_accessed < cutoff).all()
        for site in sites:
            site_dir = os.path.join(
                current_app.config["UPLOAD_FOLDER"], str(site.user_id), str(site.id)
            )
            if os.path.exists(site_dir):
                shutil.rmtree(site_dir)
            db.session.delete(site)
        db.session.commit()


def list_files(directory):
    try:
        return os.listdir(directory)
    except FileNotFoundError:
        return []
