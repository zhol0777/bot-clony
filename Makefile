start:
	.venv/bin/python ./main.py

################
# installation #
################

install: venv install-requirements

venv:
	python3 -m venv .venv
	.venv/bin/python -m pip install -U pip uv

install-requirements:
	.venv/bin/python -m uv pip compile pyproject.toml --extra dev --output-file requirements.txt
	.venv/bin/python -m uv pip install -U -r requirements.txt

update-requirements:
	.venv/bin/python -m uv pip freeze > requirements-frozen.txt

###########
# testing #
###########

test: # lint
	.venv/bin/python -m unittest discover tests

lint: ruff ty

ruff:
	.venv/bin/python -m ruff check cogs/ tests/ *.py

ty:
	.venv/bin/python -m ty check cogs/ tests/ *.py

pylint:
	.venv/bin/python -m pylint cogs/ tests/ *.py

mypy:
	.venv/bin/python -m mypy cogs/ tests/ *.py

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
