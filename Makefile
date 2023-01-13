compile-dev:
	pip-compile --extra=dev pyproject.toml --output-file requirements-dev.txt

compile:
	pip-compile pyproject.toml --output-file requirements.txt

upgrade:
	pip-compile --upgrade pyproject.toml --output-file requirements.txt

upgrade-dev:
	pip-compile --extra=dev --upgrade pyproject.toml --output-file requirements-dev.txt

install:
	pip install -r requirements.txt .

install-dev:
	pip install -r requirements-dev.txt -e .

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
