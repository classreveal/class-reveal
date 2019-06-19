FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.8

RUN pip install flask-cors

COPY ./app /app
WORKDIR /app/

EXPOSE 80
