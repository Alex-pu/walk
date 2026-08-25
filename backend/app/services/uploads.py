import os

from flask import current_app


def upload_folder():
    return current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.abspath(os.path.join(current_app.instance_path, "uploads")),
    )
