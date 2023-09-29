# granmark

## What is this?

A stripped-down version of bot-clony for other servers.

## How do I run this?

1. `cp .env-example .env` and modify values as needed
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -U -r requirements.txt`
5. `python3 ./main.py`

or, you build with docker like this

3. `docker build --no-cache -t granmarkbot .`
4. `docker-compose up -d`

Maybe it also runs on heroku. I don't know, I just followed some guide I found
on Medium to prepare it for that.
