FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine

COPY ./app /app

RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apk del build-dependencies

