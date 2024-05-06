FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update -y && apt -y upgrade && \
    apt-get install -y gcc python3 python3-pip build-essential pkg-config

WORKDIR /app

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

EXPOSE 8000

COPY . ./

COPY entrypoint.sh .

CMD bash -C 'entrypoint.sh'; 'bash'