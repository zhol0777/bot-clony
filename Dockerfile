FROM python:3.12-alpine

RUN apk update
RUN apk --no-cache add git

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

RUN git clone https://github.com/zhol0777/bot-clony.git .

RUN git checkout pasture

RUN pip install uv
RUN uv venv
RUN uv sync
CMD ["python3", "./main.py"]
