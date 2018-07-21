FROM openmatchmaking/docker-base-python-image:3.7
RUN apt-get update && apt-get install -y --reinstall build-essential

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY auth /app
WORKDIR /app
