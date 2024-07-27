start: source
	python3 ./main.py

source:
	source venv/bin/activate

################
# installation #
################

install: venv install-requirements source

venv:
	python3 -m venv venv

install-requirements: source
	python3 -m pip install -U -r requirements.txt

install-unfrozen:
	python3 -m pip install -U -r requirements-unfrozen.txt

update-requirements:
	pip freeze > requirements.txt

###########
# testing #
###########

test: lint
	python3 -m unittest discover tests

lint: ruff pylint mypy

ruff:
	python3 -m ruff check cogs/ tests/ *.py --config tests/ruff.toml

pylint:
	python3 -m pylint cogs/ tests/ *.py

mypy:
	python3 -m mypy cogs/ tests/ *.py --config-file tests/mypy.ini

##########
# docker #
##########

docker-build:
	docker build --no-cache -t bot-clony .

docker-run:
	docker-compose up -d

container-restart:
	docker-compose down
	docker-compose up -d