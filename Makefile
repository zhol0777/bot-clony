start: source
	python3 ./main.py

source:
	source venv/bin/activate

################
# installation #
################

install: venv install-requirements source

venv:
	pip install uv
	uv venv

install-requirements: source
	uv pip install --system -r requirements.txt

update-requirements:
	uv pip freeze > requirements-frozen.txt

###########
# testing #
###########

test: # lint
	# just needed for test on python 3.13...
	# uv pip install audioop-lts
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
