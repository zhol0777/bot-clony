FROM python:3

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

COPY . .

RUN python3 -m venv venv
RUN python3 -m pip install -U -r requirements.txt
RUN python3 ./main.py