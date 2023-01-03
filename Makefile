compile-dev:
	pip-compile --extra=dev pyproject.toml --output-file requirements-dev.txt

compile:
	pip-compile pyproject.toml --output-file requirements.txt

install:
	pip install -r requirements-dev.txt -e .

start:
	python rbot

fmt:
	pre-commit run --all-files
