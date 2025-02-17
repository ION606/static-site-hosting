# current_app/routes.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    abort,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.exceptions import NotFound
from datetime import datetime, timedelta
import os
import shutil
from .models import db, User, Site
from .upload import handle_upload

main_routes = Blueprint("main", __name__)


# Context processor
@main_routes.app_context_processor
def inject_subdomain():
    host = request.host
    server_parts = current_app.config["SERVER_NAME"].split(".")
    host_parts = host.split(".")

    subdomain = None
    if host_parts[-len(server_parts) :] == server_parts:
        subdomain_parts = host_parts[: -len(server_parts)]
        if subdomain_parts:
            subdomain = ".".join(subdomain_parts)

    return {
        "SUBDOMAIN": subdomain,
        "FULL_DOMAIN": host,
        "SERVERNAME": current_app.config["SERVER_NAME"],
    }


# Route definitions
@main_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            session.permanent = True
            return redirect(url_for("main.dashboard"))
        flash("Invalid email or password")
    return render_template("login.html")


@main_routes.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@main_routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("main.register"))

        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("main.dashboard"))
    return render_template("register.html")


@main_routes.route("/dashboard")
@login_required
def dashboard():
    sites = Site.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "dashboard.html",
        sites=sites,
        subdomain=request.host.split(".")[0],
        hostname=current_app.config["SERVER_NAME"],
    )


@main_routes.route("/upload", methods=["POST"])
@login_required
def upload_site():
    site_name = request.form.get("name")
    subdomain = request.form.get("subdomain").strip().lower()
    files = request.files.getlist("files")
    return handle_upload(current_user, site_name, subdomain, files)


@main_routes.route("/edit/<int:site_id>", methods=["GET", "POST"])
@login_required
def edit_site(site_id):
    site = Site.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        return "Unauthorized", 403

    site_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
    )

    if request.method == "POST":
        site.name = request.form.get("name", site.name)
        db.session.commit()

        for filename, content in request.form.items():
            if filename.endswith((".html", ".css", ".js")):
                filepath = os.path.join(site_dir, filename)
                with open(filepath, "w") as f:
                    f.write(content)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True, "message": "Site updated successfully!"})

        flash("Site updated successfully!", "success")
        return redirect(url_for("main.edit_site", site_id=site.id))

    files = {}
    for file in os.listdir(site_dir):
        with open(os.path.join(site_dir, file), "r") as f:
            files[file] = f.read()

    return render_template("edit.html", site=site, files=files)


@main_routes.route("/delete/<int:site_id>", methods=["POST"])
@login_required
def delete_site(site_id):
    site = Site.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        return "Unauthorized", 403

    site_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
    )
    if os.path.exists(site_dir):
        shutil.rmtree(site_dir)

    db.session.delete(site)
    db.session.commit()
    return redirect(url_for("main.dashboard"))


@main_routes.route("/delete_file/<int:site_id>/<filename>", methods=["POST"])
@login_required
def delete_file(site_id, filename):
    site = Site.query.get_or_404(site_id)
    if site.user_id != current_user.id:
        return "Unauthorized", 403

    site_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
    )
    file_path = os.path.join(site_dir, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"File '{filename}' deleted successfully!", "success")
    else:
        flash(f"File '{filename}' not found!", "error")

    return redirect(url_for("main.dashboard"))


@main_routes.route("/", subdomain="<subdomain>", defaults={"filename": "index.html"})
@main_routes.route("/<path:filename>", subdomain="<subdomain>")
def serve_site_content(subdomain, filename):
    if is_default_route(request.host):
        abort(404)

    site = Site.query.filter_by(subdomain=subdomain).first_or_404()
    site.last_accessed = datetime.utcnow()
    db.session.commit()

    site_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], str(site.user_id), str(site.id)
    )

    if ".." in filename or filename.startswith("/") or not os.path.exists(site_dir):
        abort(404)

    try:
        return send_from_directory(site_dir, filename)
    except NotFound:
        if "." not in filename:
            try:
                return send_from_directory(site_dir, f"{filename}.html")
            except NotFound:
                return send_from_directory(site_dir, "index.html")
        abort(404)


@main_routes.route("/")
def home():
    if not is_default_route(request.host):
        abort(404)
    return render_template("home.html")


# Helper functions
def is_default_route(hostname: str):
    if hostname == current_app.config["SERVER_NAME"]:
        return True

    parts = hostname.split(".")
    server_parts = current_app.config["SERVER_NAME"].split(".")

    if parts[-len(server_parts) :] != server_parts:
        return False

    subdomain = ".".join(parts[: -len(server_parts)])
    return (
        any(
            part in current_app.config["RESERVED_SUBDOMAINS"]
            for part in subdomain.split(".")
        )
        or subdomain in current_app.config["RESERVED_SUBDOMAINS"]
    )


# Error handler (would typically be registered in current_app factory)
@main_routes.app_errorhandler(404)
def page_not_found(_):
    host = request.host
    server_name = current_app.config["SERVER_NAME"]
    server_parts = server_name.split(".")
    host_parts = host.split(".")
    show_domain = False

    if host == server_name:
        show_domain = True
    else:
        if host_parts[-len(server_parts) :] == server_parts:
            subdomain = ".".join(host_parts[: -len(server_parts)])
            if subdomain and subdomain not in current_app.config["RESERVED_SUBDOMAINS"]:
                if not Site.query.filter_by(subdomain=subdomain).first():
                    show_domain = True

    return (
        render_template(
            "404.html",
            domain=host if show_domain else None,
            is_main_domain=(host == server_name),
        ),
        404,
    )
