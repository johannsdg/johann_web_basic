# Copyright (c) 2020-present, The Johann Web Basic Authors. All Rights Reserved.
# Use of this source code is governed by a BSD-3-clause license that can
# be found in the LICENSE file. See the AUTHORS file for names of contributors.


DOCKER_COMPOSE = docker-compose -p johann -f docker-compose.yml
DOCKER_COMPOSE_DEV = $(DOCKER_COMPOSE) -f docker-compose.dev.yml
DOCKER_COMPOSE_ALL = $(DOCKER_COMPOSE) -f docker-compose.dev.yml
PRE_COMMIT = poetry run pre-commit
SAFETY = poetry run safety
TWINE = poetry run twine


# Building and running Johann
up: build
	$(DOCKER_COMPOSE) up -d

logs:
	$(DOCKER_COMPOSE_ALL) logs -f

build: prep
	$(DOCKER_COMPOSE) build

prep:
	docker network inspect johann_public > /dev/null 2>&1 || docker network create johann_public
	docker network inspect johann_servicenet > /dev/null 2>&1 || docker network create --internal johann_servicenet


# Cleanup
clean: kill
	$(DOCKER_COMPOSE_ALL) down --volumes --remove-orphans
	$(DOCKER_COMPOSE_ALL) rm -f
	docker network prune -f
	$(MAKE) clean-files

kill:
	$(DOCKER_COMPOSE_ALL) kill

clean-files:
	rm -rf build dist ./*.egg-info


# Johann development - building and running
dev: dev-build
	$(DOCKER_COMPOSE_DEV) up -d

dev-build: prep
	$(DOCKER_COMPOSE_DEV) build


# Johann development - linting
lint:
	$(PRE_COMMIT) run check-ast
	$(PRE_COMMIT) run --show-diff-on-failure

lint-all:
	$(PRE_COMMIT) run -a check-ast
	$(PRE_COMMIT) run -a --show-diff-on-failure

safety:
	$(SAFETY) check


# Johann development - other
dev-setup:
	$(PRE_COMMIT) install --install-hooks -t pre-commit -t commit-msg -t pre-push

requirements:
	poetry lock

package:
	poetry build
	$(TWINE) check dist/*

.PHONY: venv build test logs dev prep clean lint safety requirements
