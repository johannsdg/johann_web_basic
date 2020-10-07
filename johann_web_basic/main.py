# Copyright (c) 2020-present, The Johann Web Basic Authors. All Rights Reserved.
# Use of this source code is governed by a BSD-3-clause license that can
# be found in the LICENSE file. See the AUTHORS file for names of contributors.
import secrets

import logzero
import requests
from flask import abort, jsonify, render_template, request
from flask_bootstrap import Bootstrap
from werkzeug.middleware.proxy_fix import ProxyFix

from johann_web_basic import app
from johann_web_basic.scenarios import scenarios_bp


logger = logzero.setup_logger(__name__)

app.secret_key = secrets.token_hex(16)  # WTF CSRF
app.config["BOOTSTRAP_SERVE_LOCAL"] = True
logger.debug(app.config)

bootstrap = Bootstrap(app)
logger.debug(bootstrap)

app.register_blueprint(scenarios_bp)

app.wsgi_app = ProxyFix(app.wsgi_app)
logger.debug(ProxyFix)


@app.route("/")
@app.route("/index")
@app.route("/about")
def index():
    return render_template("about.html")


@app.route("/johann/scores/<scenario_name>/status_alt")
def get_score_status_alt(scenario_name):
    try:
        url = f"http://johann_conductor:5000/scores/{scenario_name}/status_alt"
        r = requests.get(url)
        if not r.ok:
            msg = f"Failed to get status_alt for score '{scenario_name}': {r.reason}"
            logger.warn(msg)
            abort(r.status_code)
        else:
            resp_json = r.json()
            # logger.debug(resp_json)

    except Exception as e:
        msg = f"Exception getting status_alt for score '{scenario_name}': {str(e)}"
        logger.warning(msg, exc_info=True)
        abort(502)

    return jsonify(resp_json)


@app.route("/johann/read_score/<scenario_name>")
def read_score(scenario_name):
    try:
        query_string = request.query_string.decode()
        url = f"http://johann_conductor:5000/read_score/{scenario_name}?{query_string}"
        logger.debug(f"read_score() request URL: {url}")
        r = requests.get(url)
        if not r.ok:
            msg = f"Failed to read score '{scenario_name}': {r.reason}"
            logger.warn(msg)
            abort(r.status_code)
        else:
            resp_json = r.json()
            # logger.debug(scenario_json)

    except Exception as e:
        msg = f"Exception reading score '{scenario_name}': {str(e)}"
        logger.warning(msg, exc_info=True)
        abort(502)

    return jsonify(resp_json)


@app.errorhandler(404)
def handle_404(_):
    return render_template("404.html"), 404


@app.errorhandler(500)
def handle_500(_):
    return render_template("500.html"), 500


@app.errorhandler(502)
def handle_502(_):
    return render_template("502.html"), 502


if __name__ == "__main__":
    # Only for debugging while developing, i.e., `make dev`
    app.run(host="0.0.0.0", debug=True, port=80)  # nosec
