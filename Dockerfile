# Dockerfile - runs both web (gunicorn) and worker (pyrogram bot) under supervisord
FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# system deps (ffmpeg, aria2, supervisor, build tools)
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends \
      ffmpeg \
      aria2 \
      supervisor \
      gcc \
      libffi-dev \
      libssl-dev \
      build-essential \
      ca-certificates \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy requirements and install first to leverage cache
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# copy project
COPY . /app

# create supervisor config dir and logs
RUN mkdir -p /var/log/supervisor

# copy supervisord.conf into image
COPY supervisord.conf /etc/supervisor/supervisord.conf

# expose default port (Koyeb sets $PORT; gunicorn will bind to $PORT)
EXPOSE 8000

# run supervisord in foreground
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
