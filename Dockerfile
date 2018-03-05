FROM openmatchmaking/docker-base-python-image:latest

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY auth /app
WORKDIR /app
