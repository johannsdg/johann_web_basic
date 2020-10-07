# Copyright (c) 2020-present, The Johann Web Basic Authors. All Rights Reserved.
# Use of this source code is governed by a BSD-3-clause license that can
# be found in the LICENSE file. See the AUTHORS file for names of contributors.
import json
from io import StringIO

import requests
import ruamel.yaml
from flask import Blueprint, abort, make_response, redirect, render_template, url_for
from logzero import logger
from wtforms import FormField, SubmitField

from johann_web_basic.scenarios.forms import LaunchScenarioForm, PlayerForm


scenarios_bp = Blueprint("scenarios", __name__, template_folder="templates")
yaml = ruamel.yaml.YAML(typ="safe")
yaml.default_flow_style = False


@scenarios_bp.route("/scenarios", methods=["GET"])
def scenarios():
    scenarios = {}
    try:
        r = requests.get("http://johann_conductor:5000/scores")
        if not r.ok:
            msg = "Failed to get scores from Johann: {}".format(r.reason)
            logger.warn(msg)
            abort(r.status_code)

        scenarios = r.json()["data"]

    except Exception as e:
        msg = "Exception checking Johann for scores: {}".format(str(e))
        logger.warn(msg)
        logger.exception(e)
        abort(502)

    resp = make_response(
        render_template(
            "scenarios.html",
            title="Scenarios",
            data=scenarios,
        )
    )

    return resp


@scenarios_bp.route("/scenarios/<scenario_name>", methods=["GET"])
def view_scenario(scenario_name):
    scenario = {}
    try:
        r = requests.get("http://johann_conductor:5000/scores/{}".format(scenario_name))
        if not r.ok:
            msg = "Failed to get score from Johann: {}".format(r.reason)
            logger.warn(msg)
            abort(r.status_code)

        scenario = r.json()["data"]

        r = requests.get(
            "http://johann_conductor:5000/scores/{}/get_raw".format(scenario_name)
        )
        if not r.ok:
            msg = "Failed to get raw score from Johann: {}".format(r.reason)
            logger.warn(msg)
            abort(r.status_code)

        scenario_raw = r.json()["data"]

    except Exception as e:
        msg = "Exception getting score from Johann: {}".format(str(e))
        logger.warn(msg)
        logger.exception(e)
        abort(502)

    # class F(FlaskForm):
    #    json = TextAreaField(default=json.dumps(scenario, indent=4, sort_keys=True))
    #    json.disabled=True
    #    json.label = None

    ruamel_is_stupid = StringIO()
    ruamel.yaml.round_trip_dump(scenario, ruamel_is_stupid)
    data = {
        "name": scenario_name,
        "json_string": json.dumps(scenario, indent=4, sort_keys=False),
        "yaml_string": ruamel_is_stupid.getvalue(),
        "raw_json_string": json.dumps(scenario_raw, indent=4, sort_keys=False),
    }

    resp = make_response(
        render_template(
            "view_scenario.html",
            title="View Scenario",
            #        form=F(),
            data=data,
        )
    )

    return resp


@scenarios_bp.route("/scenarios/<scenario_name>/launch", methods=["GET", "POST"])
def launch_scenario(scenario_name):
    scenario_dict = {}
    try:
        r = requests.get("http://johann_conductor:5000/scores/{}".format(scenario_name))
        if not r.ok:
            msg = "Failed to get score '{}' from Johann: {}".format(
                scenario_name, r.reason
            )
            logger.warn(msg)
            abort(r.status_code)

        scenario_dict = r.json()["data"]

        if scenario_dict is None:
            msg = "Received 'None' for scenario '{}'".format(scenario_dict)
            logger.warn(msg)
            abort(500)

    except Exception as e:
        msg = "Exception getting score '{}' from Johann: {}".format(
            scenario_name, str(e)
        )
        logger.warn(msg)
        logger.exception(e)
        abort(502)

    johann_hosts = {}
    try:
        r = requests.get("http://johann_conductor:5000/hosts")
        if not r.ok:
            msg = "Failed to get hosts from Johann: {}".format(r.reason)
            logger.warn(msg)
            abort(r.status_code)

        johann_hosts = r.json()["data"].keys()

        if johann_hosts is None:
            msg = "Received 'None' for johann hosts"
            logger.warn(msg)
            abort(500)

    except Exception as e:
        msg = "Exception getting hosts from Johann: {}".format(str(e))
        logger.warn(msg)
        logger.exception(e)
        abort(502)

    hosts = []
    for h in johann_hosts:
        if h not in hosts:
            hosts.append(h)
        else:
            logger.warn("Duplicate host found: {}".format(h))
    if hosts is not None:
        hosts.sort()

    host_choices = [(h, h) for h in hosts]

    # subclass to dynamically populate fields based on scenario
    class F(LaunchScenarioForm):
        pass

    for player_name, _ in scenario_dict["players"].items():
        player_form = FormField(PlayerForm)
        setattr(F, player_name, player_form)

    # do this last so it's at the bottom
    setattr(  # noqa
        F,
        "submit",
        SubmitField("Launch Scenario", validators=[F.player_uniqueness, F.roll_call]),
    )

    formdata = scenario_dict["players"]

    logger.debug("Populating form using this data:\n{}".format(formdata))

    form = F(name=scenario_name, data=formdata)
    form.description.data = scenario_dict["description"]
    # form.name.render_kw = {'disabled': 'disabled'}

    for player_name in list(scenario_dict["players"].keys()):
        form[player_name]["hosts"].choices += host_choices

    if form.validate_on_submit():
        return redirect(
            url_for(
                "scenarios.actually_launch_scenario",
                scenario_name=scenario_name,
                _external=True,
                _scheme="http",
            )
        )

    resp = make_response(
        render_template(
            "launch_scenario.html",
            title="Launch Scenario",
            form=form,
        )
    )

    return resp


@scenarios_bp.route("/scenarios/<scenario_name>/actually_launch", methods=["GET"])
def actually_launch_scenario(scenario_name):
    try:
        url = "http://johann_conductor:5000/affrettando/{}".format(scenario_name)
        logger.debug("playing score from UI with url: {}".format(url))
        r = requests.get(url)
        if not r.ok:
            msg = "Failed to play score '{}' ({}):\n{}".format(
                scenario_name, r.reason, json.dumps(r.json(), indent=4, sort_keys=False)
            )
            logger.warn(msg)
            abort(r.status_code)
        else:
            return redirect(
                url_for(
                    "scenarios.scenario_status",
                    scenario_name=scenario_name,
                    _external=True,
                    _scheme="http",
                )
            )

    except Exception as e:
        msg = "Exception playing score '{}': {}".format(scenario_name, str(e))
        logger.warn(msg)
        logger.exception(e)
        abort(502)


@scenarios_bp.route("/scenarios/<scenario_name>/status", methods=["GET"])
def scenario_status(scenario_name):
    scenario_json = {"name": scenario_name}
    try:
        url = "http://johann_conductor:5000/scores/{}/get_raw".format(scenario_name)
        r = requests.get(url)
        if not r.ok:
            msg = "Failed to get score '{}': {}".format(scenario_name, r.reason)
            logger.warn(msg)
            abort(r.status_code)
        else:
            scenario_json = r.json()["data"]
            # logger.debug(scenario_json)

    except Exception as e:
        msg = "Exception getting score '{}': {}".format(scenario_name, str(e))
        logger.warn(msg)
        logger.exception(e)
        abort(502)

    resp = make_response(
        render_template(
            "scenario_status.html", title="Scenario Status", data=scenario_json
        )
    )

    return resp


@scenarios_bp.route("/scenarios/<scenario_name>/status_raw", methods=["GET"])
def scenario_status_raw(scenario_name):
    resp = make_response(
        render_template(
            "scenario_status_raw.html",
            title="Scenario Status (Raw)",
            data=scenario_name,
        )
    )

    return resp
