FROM python:3.13-alpine

RUN apk update
RUN apk --no-cache add git uv

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

RUN git clone https://github.com/zhol0777/bot-clony.git .

RUN git checkout bot-lite

RUN uv venv
RUN uv sync
CMD [".venv/bin/python", "./main.py"]
