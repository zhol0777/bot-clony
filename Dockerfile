FROM python:3.13-alpine

RUN apk update
RUN apk --no-cache add uv \
    build-base \
    sqlcipher-dev \
    libffi-dev

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

# Build from the local working directory (docker build context),
# not from a remote repository.
COPY . .

RUN uv venv
RUN uv sync
CMD [".venv/bin/python", "./main.py"]