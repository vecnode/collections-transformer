import os
import re
import logging

from flask import request
from flask import jsonify
from flask import session
from bson.objectid import ObjectId
from bson import json_util
import json
import api.models as models
import api.llm_modelling as llm
from app import model
from flask import Blueprint
import traceback
from . import provider_ollama
from pathlib import Path
from config import settings


endpoints_bp = Blueprint('endpoints', __name__)
logger = logging.getLogger(__name__)


def _log_print(*args, **kwargs):
    logger.info(" ".join(str(arg) for arg in args))


print = _log_print


def parse_json(data):
    return json.loads(json_util.dumps(data))


# Load route modules in-order into this module namespace to preserve endpoint behavior.
_ROUTES_PARTS_DIR = Path(__file__).with_name("routes")
_ROUTES_PART_FILES = [
    "core_crud.py",
    "agents.py",
    "system_db.py",
    "auth_user.py",
    "analysis_and_tests.py",
]

for _part_file in _ROUTES_PART_FILES:
    _part_path = _ROUTES_PARTS_DIR / _part_file
    with _part_path.open("r", encoding="utf-8") as _f:
        exec(compile(_f.read(), str(_part_path), "exec"), globals())


del _part_file, _part_path, _f
