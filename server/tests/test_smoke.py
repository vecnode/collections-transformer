from pathlib import Path
import sys


SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

import api


def test_create_app_smoke(monkeypatch):
    fake_client = object()
    fake_db = {}

    monkeypatch.setattr(api, "connect_to_mongodb", lambda uri, database: (fake_client, fake_db))
    monkeypatch.setattr(api, "setup_gridfs", lambda database: object())
    monkeypatch.setattr(api, "setup_api_endpoints", lambda app: None)
    monkeypatch.setattr(api, "setup_ml_modelling", lambda model: None)

    app = api.create_app("dual")

    assert app is not None
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
