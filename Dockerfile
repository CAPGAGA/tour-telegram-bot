# Building base image to then split into web and bot container
FROM python:3.9-slim as base_image

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Update all package managers
RUN apt-get update -y && apt -y upgrade
RUN pip install pip --upgrade

COPY requirements.txt .

RUN pip install --no-cache -r requirements.txt

COPY ./settings.py .

# Copy needed file for api
FROM base_image as web

COPY ./api /api
COPY ./db  /db
COPY ./web /web

# Copy needed files for bot
FROM base_image as bot

COPY ./bot /bot

