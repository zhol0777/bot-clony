FROM python:3.12-slim

RUN apt update
RUN apt install -y git build-essential locales locales-all
RUN locale-gen en_US.utf8

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

RUN git clone https://github.com/zhol0777/bot-clony.git .

RUN git checkout bot-lite

RUN pip install uv
RUN uv pip install --system -r requirements.txt
CMD ["python3", "./main.py"]
