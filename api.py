#!/usr/bin/env python3

import os
import traceback
import csv
import random
import json
import hashlib

from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
from flask_restplus import Api, Resource
from flask_restplus import abort
from flask_caching import Cache
from loguru import logger
from requests import codes as http_codes
from api.commons import configuration
#from api.tech.SmokeTest import SmokeTest

CACHE_TTL = 60  # 60 seconds

# Load conf
conf = configuration.load()
script_dir = os.path.dirname(__file__)
# tableau de résultat
participants_response = {}
result = []

def _init_app(p_conf):
    # Load app config into Flask WSGI running instance
    r_app = Flask(__name__)
    r_app.config["API_CONF"] = p_conf

    # Authorize Cross-origin (CORS)
    r_app.config["CORS_HEADERS"] = "Auth-Token, Content-Type, User, Content-Length"
    CORS(r_app, resources={r"/*": {"origins": "*"}})

    blueprint = Blueprint("api", __name__)
    r_swagger_api = Api(
        blueprint,
        doc="/" + p_conf["url_prefix"] + "/doc/",
        title="API",
        description="Chrono course API",
    )
    r_app.register_blueprint(blueprint)
    r_ns = r_swagger_api.namespace(
        name=p_conf["url_prefix"], description="Api documentation"
    )

    # lecture du fichier des noms
    with open('data/participants3.csv', 'r', encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='|')

        # les clés qui vont nous servir à créer nos dictionnaires
        keys = None
        for row in csvreader:
            # la première ligne va servir pour les clés de nos dictionnaires pythons
            if not(keys):
                keys = row
            else:
                # on transforme les lignes suivantes en dictionnaire
                dictionnary = dict(zip(keys, row))
                # on l’ajoute au tableau
                result.append(dictionnary)

    return r_app, r_swagger_api, r_ns


app, swagger_api, ns = _init_app(conf)

# Init cache
cache = Cache(app, config={"CACHE_TYPE": "simple"})

#smoke = SmokeTest()

# Load files


# Access log query interceptor
@app.before_request
def access_log():
    logger.info("{0} {1}".format(request.method, request.path))


@ns.route("/", strict_slashes=False)
class Base(Resource):
    @staticmethod
    def get():
        """
            Base route
        """
        response = {"status_code": http_codes.OK, "message": "Api chrono course"}

        return make_reponse(response, http_codes.OK)


@ns.route("/heartbeat")
class Heart(Resource):
    @staticmethod
    def get():
        """
            Heartbeat
            Are you alive ?
        """
        response = {"status_code": http_codes.OK, "message": "Heartbeat"}

        return make_reponse(response, http_codes.OK)


@ns.route("/supervision")
class Supervision(Resource):
    @staticmethod
    def get():
        """
            Api configuration
        """
        response = None
        try:
            response = app.config["API_CONF"]
        except Exception:
            abort(http_codes.SERVER_ERROR, "Can't get the configuration")

        return _success(response)


@ns.route("/smokeTest")
class SmokeTest(Resource):
    @staticmethod
    def get():
        """
            SmokeTest
        """
        response = None
        try:
            response = smoke.get_results(poterie_classifier)
        except Exception:
            abort(http_codes.SERVER_ERROR, "Can't get the model")

        return _success(response)


# Doc for parking/next_filling route
participants_route_parser = swagger_api.parser()


@swagger_api.expect(participants_route_parser)
@ns.route("/participants", endpoint="/participants")
class Participants(Resource):
    @staticmethod
    #@cache.cached(timeout=CACHE_TTL, key_prefix="/participants")
    def get():
        logger.debug("No cache used")
        course = "defaut"
        if 'course' in request.args:
            course = request.args['course']

        hash_course = string_to_int(course.encode('utf-8'))
        nb_participants = max(140, hash_course % 500)
        index_depart = hash_course % 60000
        index_fin = index_depart + nb_participants + 1
        
        participants_response["course"] = course
        participants_response["nb_participants"] = nb_participants
        participants_response["participants"] = result[index_depart:index_fin]

        response = participants_response

        return make_reponse(response, http_codes.OK)

    @staticmethod
    def post():
        raw = request.json["raw"]
        response = "participant created"

        return make_reponse(response, http_codes.OK)

@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def _success(response):
    return make_reponse(response, http_codes.OK)


def _failure(exception, http_code=http_codes.SERVER_ERROR):
    try:
        exn = traceback.format_exc(exception)
        logger.info("EXCEPTION: {}".format(exn))
    except Exception as e:
        logger.info("EXCEPTION: {}".format(exception))
        logger.info(e)

    try:
        data, code = exception.to_tuple()
        return make_reponse(data, code)
    except:
        try:
            data = exception.to_dict()
            return make_reponse(data, exception.http)
        except Exception:
            return make_reponse(None, http_code)


def make_reponse(p_object=None, status_code=http_codes.OK):
    if p_object is None and status_code == http_codes.NOT_FOUND:
        p_object = {
            "status": {
                "status_content": [
                    {"code": "404 - Not Found", "message": "Resource not found"}
                ]
            }
        }

    json_response = jsonify(p_object)
    json_response.status_code = status_code
    json_response.content_type = "application/json;charset=utf-8"
    json_response.headers["Cache-Control"] = "max-age=3600"
    return json_response

def string_to_int(s):
    #ord3 = lambda x : '%.3d' % ord(x)
    #entier = int(''.join(map(ord3, s)))
    #return entier
    return int(hashlib.md5(s).hexdigest()[:16], 16)

def get_participants(raw: list) -> dict:
    try:

        response = {
            "participants": [
                {
                    "nom": "Dupont",
                    "prenom": "toto1"
                },
                {
                    "nom": "Dupont",
                    "prenom": "toto1"
                },
                {
                    "nom": "Dupont",
                    "prenom": "toto1"
                },
            ],
        }
        logger.info(response)

        response = json.dumps(result[1:4]) # Tous les elements de 1 a 3

        return response
    except Exception:
        abort(http_codes.SERVER_ERROR, "Can't get a participant")


if __name__ == "__main__":
    #cf_port = os.getenv("PORT")
    cf_port = conf["port"]
    if cf_port is None:
        app.run(host="localhost", port=5001, debug=True)
    else:
        app.run(host="localhost", port=int(cf_port), debug=True)
