from flask import (
	Flask,
	render_template,
	request,
	redirect,
	url_for,
	send_from_directory,
	flash,
	abort,
	jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
	LoginManager,
	UserMixin,
	login_user,
	logout_user,
	login_required,
	current_user,
)
from flask_apscheduler import APScheduler
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import NotFound
import os
import shutil
from datetime import datetime, timedelta
from waitress import serve
import re
from secrets import token_hex

app = Flask(__name__)

try:
	with open("/app/instance/secret.key", "rb") as f:
		app.config["SECRET_KEY"] = bytes.hex(f.readline())
except FileNotFoundError as e:
	if not os.path.exists("/app/instance"):
		os.mkdir("/app/instance")

	with open("/app/instance/secret.key", "wb") as f:
		newKey = token_hex(64)
		f.write(bytearray.fromhex(newKey))
		app.config["SECRET_KEY"] = newKey

PORT = 5121
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////app/instance/db.sqlite"
app.config["UPLOAD_FOLDER"] = "sites"
app.config["SERVER_NAME"] = "tinysite.cloud"
app.config["SESSION_COOKIE_DOMAIN"] = ".tinysite.cloud"
db = SQLAlchemy(app)


RESERVED_SUBDOMAINS = {
	"",
	"www",
	"api",
	"admin",
	"support",
	"docs",
	"blog",
	"cdn",
	"test",
	"dev",
	"staging",
	"secure",
	"mail",
	"status",
	"gateway",
}


# TODO: add specific page redirects here as they're added
def isDefaultRoute(hostname: str):
	if hostname.count(".") < 2:
		return True

	subdomain = hostname.split(".")[0]
	return not subdomain or subdomain in RESERVED_SUBDOMAINS


# Models
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(100), unique=True)
	password_hash = db.Column(db.String(128))  # Renamed for clarity

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)


class Site(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
	name = db.Column(db.String(100))
	subdomain = db.Column(db.String(100), unique=True)
	last_accessed = db.Column(db.DateTime)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.errorhandler(404)
def page_not_found(_):
	return render_template("404.html", domain=request.host), 404


# Auth setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


# Scheduler for auto-deletion
scheduler = APScheduler()
scheduler.init_app(app)


def delete_inactive_sites():
	with app.app_context():
		cutoff = datetime.utcnow() - timedelta(days=30)
		sites = Site.query.filter(Site.last_accessed < cutoff).all()
		for site in sites:
			site_dir = os.path.join(
				app.config["UPLOAD_FOLDER"], str(site.user_id), str(site.id)
			)
			if os.path.exists(site_dir):
				shutil.rmtree(site_dir)
			db.session.delete(site)
		db.session.commit()


if not scheduler.running:
	scheduler.start()
	scheduler.add_job(
		id="delete_job", func=delete_inactive_sites, trigger="interval", days=1
	)


# Routes
@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		email = request.form.get("email")
		password = request.form.get("password")
		user = User.query.filter_by(email=email).first()

		if user and user.check_password(password):
			login_user(user)
			return redirect(url_for("dashboard"))
		flash("Invalid email or password")
	return render_template("login.html")


@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		email = request.form.get("email")
		password = request.form.get("password")

		if User.query.filter_by(email=email).first():
			flash("Email already exists")
			return redirect(url_for("register"))

		new_user = User(email=email)
		new_user.set_password(password)
		db.session.add(new_user)
		db.session.commit()

		login_user(new_user)
		return redirect(url_for("dashboard"))
	return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
	sites = Site.query.filter_by(user_id=current_user.id).all()
	return render_template(
		"dashboard.html",
		sites=sites,
		subdomain=request.host.split(".")[0],
		hostname=app.config["SERVER_NAME"],
	)


@app.route("/upload", methods=["POST"])
@login_required
def upload_site():
	site_name = request.form.get("name")
	subdomain = request.form.get("subdomain").strip().lower()  # normalize to lowercase

	# Subdomain validation
	if not re.match(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", subdomain):
		flash(
			"Invalid subdomain. Use lowercase letters, numbers, and hyphens.", "error"
		)
		return redirect(url_for("dashboard"))

	if not site_name or not subdomain:
		flash("Site name and URL subdomain are required", "error")
		return redirect(url_for("dashboard"))

	# Check subdomain availability
	if Site.query.filter_by(subdomain=subdomain).first():
		flash("This URL is already taken", "error")
		return redirect(url_for("dashboard"))

	# Check if index.html is included
	files = request.files.getlist("files")
	if not any(file.filename == "index.html" for file in files):
		flash("You must include an index.html file", "error")
		return redirect(url_for("dashboard"))

	# Create site directory
	site = Site(user_id=current_user.id, name=site_name, subdomain=subdomain)
	db.session.add(site)
	db.session.commit()

	site_dir = os.path.join(
		app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
	)
	os.makedirs(site_dir, exist_ok=True)

	# Save uploaded files
	for file in files:
		if file.filename == "":
			continue
		file.save(os.path.join(site_dir, file.filename))

	flash("Site created successfully!", "success")
	return redirect(url_for("dashboard"))


@app.route("/edit/<int:site_id>", methods=["GET", "POST"])
@login_required
def edit_site(site_id):
	site = Site.query.get_or_404(site_id)
	if site.user_id != current_user.id:
		return "Unauthorized", 403

	site_dir = os.path.join(
		app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
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
		return redirect(url_for("edit_site", site_id=site.id))

	files = {}
	for file in os.listdir(site_dir):
		with open(os.path.join(site_dir, file), "r") as f:
			files[file] = f.read()

	return render_template("edit.html", site=site, files=files)


@app.route("/delete/<int:site_id>", methods=["POST"])
@login_required
def delete_site(site_id):
	site = Site.query.get_or_404(site_id)
	if site.user_id != current_user.id:
		return "Unauthorized", 403

	site_dir = os.path.join(
		app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
	)
	if os.path.exists(site_dir):
		shutil.rmtree(site_dir)

	db.session.delete(site)
	db.session.commit()
	return redirect(url_for("dashboard"))


@app.route("/delete_file/<int:site_id>/<filename>", methods=["POST"])
@login_required
def delete_file(site_id, filename):
	# Get the site and verify ownership
	site = Site.query.get_or_404(site_id)
	if site.user_id != current_user.id:
		return "Unauthorized", 403

	# Build the file path
	site_dir = os.path.join(
		app.config["UPLOAD_FOLDER"], str(current_user.id), str(site.id)
	)
	file_path = os.path.join(site_dir, filename)

	# Delete the file if it exists
	if os.path.exists(file_path):
		os.remove(file_path)
		flash(f"File '{filename}' deleted successfully!", "success")
	else:
		flash(f"File '{filename}' not found!", "error")

	return redirect(url_for("dashboard"))


# use subdomains
@app.route("/", subdomain="<subdomain>", defaults={"filename": "index.html"})
@app.route("/<path:filename>")
def serve_site_content(filename):
	subdomain = request.host.split(".")[0]

	site = Site.query.filter_by(subdomain=subdomain).first_or_404()
	site.last_accessed = datetime.utcnow()
	db.session.commit()

	site_dir = os.path.join(
		app.config["UPLOAD_FOLDER"], str(site.user_id), str(site.id)
	)

	if isDefaultRoute(request.host):
		return send_from_directory("index.html")

	# Security check
	if ".." in filename or filename.startswith("/") or not os.path.exists(site_dir):
		return render_template("404.html"), 404

	try:
		return send_from_directory(site_dir, filename)
	except NotFound:
		if "." not in filename:
			try:
				return send_from_directory(site_dir, f"{filename}.html")
			except NotFound:
				redirect(app.config["SERVER_NAME"])
				return send_from_directory(site_dir, "index.html")
		abort(404)


def list_files(directory):
	try:
		return os.listdir(directory)
	except FileNotFoundError:
		return []


@app.context_processor
def inject_utilities():
	return dict(list_files=list_files)


@app.route("/")
def home():
	if isDefaultRoute(request.host):
		return render_template("home.html")
	else:
		return serve_site_content("index.html")


if __name__ == "__main__":
	os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
	with app.app_context():
		db.create_all()
		serve(app, host="0.0.0.0", port=PORT)
