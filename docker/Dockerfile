FROM python:3.10

RUN mkdir /app

COPY ./requirements.txt /app/requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app/src

RUN  pip install --upgrade pip \
     && pip install -r /app/requirements.txt

COPY .flake8 /app/
COPY  src /app/src

WORKDIR app/src
