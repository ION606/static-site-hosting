from waitress import serve
import os
from app import create_app, db, config

app = create_app()

if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    print(f"listening on port {config.Config.PORT}")

    with app.app_context():
        db.create_all()
        serve(app, host="0.0.0.0", port=config.Config.PORT)
