venv:
	python3 -m venv venv

source:
	source venv/bin/activate

install-requirements: source
	python3 -m pip install -U -r requirements.txt

install: venv install-requirements source

start: source
	python3 ./main.py

lint: flake8 mypy pylint

flake8:
	flake8 cogs/ db.py main.py util.py

pylint:
	pylint cogs/ db.py main.py util.py

mypy:
	mypy cogs/*.py db.py main.py util.py