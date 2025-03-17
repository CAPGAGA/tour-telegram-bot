# Building base image to then split into web and bot container
FROM python:3.9-slim as base_image

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Update all package managers
RUN apt-get update -y && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY ./settings.py .

# Copy needed file for api
FROM base_image as web

WORKDIR /app

COPY ./api /app/api
COPY ./db  /app/db
COPY ./web /app/web
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini
COPY ./babel.cfg /app/babel.cfg


# Copy needed files for bot
FROM base_image as bot

ENV PYTHONPATH=.

WORKDIR /app

COPY ./bot /app/bot
COPY ./babel.cfg /app/babel.cfg
