PIP_COMPILE = pip-compile

# Define a .PHONY rule to avoid conflict with file names
.PHONY: compile upgrade install start fmt test mypy

compile: compile-prod compile-dev

upgrade: upgrade-prod upgrade-dev

compile-dev:
	$(PIP_COMPILE) --extra=dev pyproject.toml --output-file requirements-dev.txt

compile-prod:
	$(PIP_COMPILE) pyproject.toml --output-file requirements.txt

upgrade-prod:
	$(PIP_COMPILE) --upgrade pyproject.toml --output-file requirements.txt

upgrade-dev:
	$(PIP_COMPILE) --upgrade pyproject.toml --all-extras --output-file requirements-dev.txt

install:
	pip install -r requirements.txt
	pip install .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

start:
	python rbot

fmt:
	pre-commit run --all-files

test:
	coverage run -m pytest --record-mode=rewrite
	python -m coverage combine
	python -m coverage report -m --skip-covered
	python -m coverage json

mypy:
	mypy rbot
