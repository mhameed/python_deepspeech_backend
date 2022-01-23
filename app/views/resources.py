import uuid
import json
import sys
import os
from flask import Blueprint, g, jsonify, abort, request, make_response, url_for, render_template, Response, send_from_directory, send_file
from sqlalchemy.exc import IntegrityError
from app import db
from ..models import Clip
import logging
logger = logging.getLogger('cv.resources')

bp = Blueprint('resources', __name__, url_prefix='/resources')

@bp.route('/<id>', methods=['GET'])
def get(id):
    logger.debug(f"get: Received a request with id:{id}")
    try:
        fname = f"{id}.mp3"
        return send_from_directory(os.path.join(os.getcwd(), 'audio'), fname, as_attachment=False, cache_timeout=30)
    except Exception as e:
        logger.debug(f"get: Could not find resource with id:{id}")
        return make_response(jsonify(status='File not found.'), 404)
