# bannerlordbot

## What is this?

A stripped-down version of bot-clony for other servers that only sets
banner.

## Why re-write it?

Kok thought it would be a good idea for the 40's server to have.

## How do I run this?

1. `cp .env-example .env` and modify values as needed
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -U -r requirements.txt`
5. `python3 ./main.py`

or, you build with docker like this

3. `docker build --no-cache -t bannerbot .`
4. `docker-compose up -d`

Maybe it also runs on heroku. I don't know, I just followed some guide I found
on Medium to prepare it for that.

## How do I use it?

Bannerlord replies to a message in the channel where banner images are chosen
with `!banner` for the first/only image in a post, or `!banner {image number}`
to pick out a specific image from a post with multiple embeds. `!banner 3` for
the third image in a post, and so on.