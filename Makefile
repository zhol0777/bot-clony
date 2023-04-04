venv:
	python3 -m venv venv

source:
	source venv/bin/activate

install-requirements: source
	python3 -m pip install -U -r requirements.txt

install: venv install-requirements source

start: source
	python3 ./main.py

lint: flake8 pylint mypy

flake8:
	flake8 cogs/ db.py main.py util.py

pylint:
	pylint cogs/ db.py main.py util.py

mypy:
	mypy cogs/*.py db.py main.py util.py

docker-build:
	docker build --no-cache -t bot-clony .

docker-run:
	docker-compose up -d

container-restart:
	docker-compose down
	docker-compose up -d

install-unfrozen:
	python3 -m pip install -U -r requirements-unfrozen.txt

update-requirements:
	pip freeze > requirements.txt