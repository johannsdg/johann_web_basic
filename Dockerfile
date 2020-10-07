# Copyright (c) 2020-present, The Johann Web Basic Authors. All Rights Reserved.
# Use of this source code is governed by a BSD-3-clause license that can
# be found in the LICENSE file. See the AUTHORS file for names of contributors.

FROM tiangolo/uwsgi-nginx-flask:python3.8

ENV STATIC_PATH /app/johann_web_basic/static
ENV PYTHONPATH=$PYTHONPATH:/app/johann_web_basic

# install poetry
RUN python3 -m pip install pipx
#RUN pipx install poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry completions bash > /etc/bash_completion.d/poetry.bash-completion

WORKDIR /app

# install dependencies
COPY poetry.lock ./
COPY pyproject.toml ./
RUN poetry install --no-dev --no-root

COPY uwsgi.ini ./

WORKDIR /app/johann_web_basic

COPY johann_web_basic/ ./
