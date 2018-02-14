FROM python:3.6-slim-stretch
RUN apt-get update && apt-get -y install gcc

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY auth /app
WORKDIR /app
