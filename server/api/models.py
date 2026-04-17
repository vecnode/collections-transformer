from api import db, grid_fs
import logging

from bson.objectid import ObjectId
import bson.binary
import json
from . import llm_modelling as llm
import pandas as pd
import copy
import random
import datetime
import json
import os
import codecs
import base64
import tempfile
import urllib.request
import shutil
import concurrent.futures
from PIL import Image
import traceback
import pytz
from pathlib import Path
from config import settings

category_collection = db["category"]
dataset_collection = db["dataset"]
item_collection = db["item"]
labelset_collection = db["labelset"]
label_collection = db["label"]
text_label_collection = db["text_label"]
resultset_collection = db["resultset"]
embedding_collection = db["embedding"]
image_collection = db["image"]
analysis_history_collection = db["analysis_history"]
agent_collection = db["agent"]

formatExamplesInsidePrompt = True
logger = logging.getLogger(__name__)


def _log_print(*args, **kwargs):
    logger.info(" ".join(str(arg) for arg in args))


print = _log_print


# Load model domains in-order into this module namespace to preserve legacy API.
_MODELS_PARTS_DIR = Path(__file__).with_name("models")
_MODELS_PART_FILES = [
    "embedding.py",
    "labelset.py",
    "binary_label.py",
    "score_label.py",
    "label.py",
    "dataset.py",
    "category.py",
    "item.py",
    "resultset.py",
    "user.py",
    "analysis_history.py",
    "agent.py",
]

for _part_file in _MODELS_PART_FILES:
    _part_path = _MODELS_PARTS_DIR / _part_file
    with _part_path.open("r", encoding="utf-8") as _f:
        exec(compile(_f.read(), str(_part_path), "exec"), globals())


del _part_file, _part_path, _f
