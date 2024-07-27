FROM python:3.11-alpine

RUN apk update
RUN apk add git

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

RUN git clone https://github.com/zhol0777/bot-clony.git .

RUN git checkout granmark

RUN pip3 install -U -r requirements-unfrozen.txt
CMD ["python3", "./main.py"]
