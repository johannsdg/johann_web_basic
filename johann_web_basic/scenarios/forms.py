# Copyright (c) 2020-present, The Johann Web Basic Authors. All Rights Reserved.
# Use of this source code is governed by a BSD-3-clause license that can
# be found in the LICENSE file. See the AUTHORS file for names of contributors.

import requests
from flask_wtf import FlaskForm
from logzero import logger
from werkzeug.datastructures import MultiDict
from wtforms import (
    HiddenField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    StringField,
)
from wtforms.validators import DataRequired, ValidationError


def dict_to_query_string(d):
    query_string = ""

    if isinstance(d, MultiDict):
        d = d.to_dict(flat=False)

    for k, v in d.items():
        if type(v) is list:
            query_string += "{}={}&".format(k, ",".join(v))
        else:
            query_string += "{}={}&".format(k, v)

    return query_string


def player_host_map(form):
    ret = {}
    for field in form:
        if type(field.data) is dict and "hosts" in field.data:
            hosts = field.data["hosts"]
            if type(hosts) is list:
                hosts = ",".join(hosts)
            player = field.id
            ret[player] = hosts
    return ret


class EmbeddedForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(EmbeddedForm, self).__init__(meta={"csrf": False}, *args, **kwargs)


class PlayerForm(EmbeddedForm):
    name = HiddenField()
    hosts = SelectMultipleField("Host Name(s)", choices=[], validators=[])
    # PLANNED: populate the select dynamically
    image = SelectField(
        "Image",
        choices=[
            ("None", "None"),
            ("johann_player", "johann_player"),
        ],
        validators=[DataRequired()],
    )
    scale = IntegerField("Number of Hosts")


class LaunchScenarioForm(FlaskForm):
    # name = StringField(render_kw={'disabled':'disabled'})
    name = HiddenField()
    description = StringField(render_kw={"disabled": "disabled"})

    def player_uniqueness(form, field):  # 'field' is ignored
        so_far = []
        duplicate = []
        for field in form:
            if type(field.data) is dict and "hosts" in field.data:
                for v in field.data["hosts"]:
                    if v in so_far and v not in duplicate:
                        duplicate.append(v)
                    else:
                        so_far.append(v)

        if len(duplicate) > 0:
            raise ValidationError(
                "hosts used more than once: {}".format(", ".join(duplicate))
            )

    def roll_call(form, field):  # 'field' is ignored
        logger.debug("roll_call validation with data: {}".format(form.data))

        data = {"create_hosts": False, "discard_hosts": False, "players": {}}
        for field in form:
            if type(field.data) is dict and "hosts" in field.data:
                data["players"][field.name] = field.data

        try:
            r = requests.post(
                "http://johann_conductor:5000/scores/{}/roll_call".format(
                    form.name.data
                ),
                json=data,
            )
            if not r.ok:
                msg = "roll_call to Johann failed ({}):\n".format(r.reason)
                try:
                    rj = r.json()
                    msg += "\n".join(rj["messages"])
                except Exception:
                    pass
                finally:
                    logger.warn(msg)
                    raise ValidationError(msg)

        except Exception as e:
            msg = "Exception validating score '{}': {}".format(form.name.data, str(e))
            logger.warn(msg)
            logger.exception(e)
            raise ValidationError(msg)
