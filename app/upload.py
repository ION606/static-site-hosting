# upload_handler.py
from flask import flash, redirect, url_for, current_app
import os
import re
from .config import Config
from .models import Site
from . import db

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per file
MAX_TOTAL_STORAGE = 100 * 1024 * 1024  # 100MB per user
ALLOWED_EXTENSIONS = {
    "html",
    "css",
    "js",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "svg",
    "ico",
    "webp",
    "txt",
    "pdf",
}
MAX_FILES_PER_UPLOAD = 50


def get_user_storage(user_id):
    total_size = 0
    user_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], str(user_id))
    if os.path.exists(user_dir):
        for site_dir in os.listdir(user_dir):
            site_path = os.path.join(user_dir, site_dir)
            if os.path.isdir(site_path):
                for root, _, files in os.walk(site_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        total_size += os.path.getsize(fp)
    return total_size


def handle_upload(current_user, site_name, subdomain, files):
    # Validation checks
    if not re.match(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", subdomain):
        flash("Invalid subdomain format", "error")
        return redirect(url_for("main.dashboard"))

    # Check for reserved subdomains
    if subdomain in Config.RESERVED_SUBDOMAINS:
        flash(f"The subdomain '{subdomain}' is reserved", "error")
        return redirect(url_for("main.dashboard"))

    if not site_name or not subdomain:
        flash("Name and subdomain required", "error")
        return redirect(url_for("main.dashboard"))

    if Site.query.filter_by(subdomain=subdomain).first():
        flash("Subdomain taken", "error")
        return redirect(url_for("main.dashboard"))

    if len(files) > MAX_FILES_PER_UPLOAD:
        flash(f"Max {MAX_FILES_PER_UPLOAD} files per upload", "error")
        return redirect(url_for("main.dashboard"))

    for file in files:
        if "." not in file.filename:
            flash(f"File {file.filename} has no extension", "error")
            return redirect(url_for("main.dashboard"))
        ext = file.filename.rsplit(".", 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            flash(f".{ext} files not allowed", "error")
            return redirect(url_for("main.dashboard"))

    total_new_size = 0
    for file in files:
        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)
        if size > MAX_FILE_SIZE:
            flash(f"{file.filename} exceeds {MAX_FILE_SIZE//1024//1024}MB", "error")
            return redirect(url_for("main.dashboard"))
        total_new_size += size

    current_storage = get_user_storage(current_user.id)
    if current_storage + total_new_size > MAX_TOTAL_STORAGE:
        flash(f"Storage limit ({MAX_TOTAL_STORAGE//1024//1024}MB) exceeded", "error")
        return redirect(url_for("main.dashboard"))

    if not any(f.filename == "index.html" for f in files):
        flash("Missing index.html", "error")
        return redirect(url_for("main.dashboard"))

    # Create site
    site = Site(user_id=current_user.id, name=site_name, subdomain=subdomain)
    db.session.add(site)
    db.session.commit()

    # Save files
    site_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
    )
    os.makedirs(site_dir, exist_ok=True)

    try:
        for file in files:
            if file.filename:
                file.save(os.path.join(site_dir, file.filename))
    except Exception as e:
        db.session.delete(site)
        db.session.commit()
        flash("Upload failed", "error")
        return redirect(url_for("main.dashboard"))

    flash("Site created!", "success")
    return redirect(url_for("main.dashboard"))

