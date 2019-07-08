FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.8

COPY ./app /app
WORKDIR /app/

RUN apk --update add python py-pip openssl ca-certificates py-openssl wget poppler-dev
RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apk del build-dependencies

EXPOSE 80
