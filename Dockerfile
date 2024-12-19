FROM python:3.11-alpine

RUN apk update
RUN apk --no-cache add git

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

RUN git clone https://github.com/zhol0777/bot-clony.git .

RUN git checkout bot-lite

RUN pip install uv
RUN uv pip install -r requirements-unfrozen.txt
CMD ["python3", "./main.py"]
