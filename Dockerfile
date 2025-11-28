FROM python:3.10.8-slim-buster

ENV DEBIAN_FRONTEND=noninteractive

# point buster repos to archive.debian.org and disable Valid-Until check
RUN sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list \
 && sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list || true \
 && echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends \
      gcc \
      libffi-dev \
      libssl-dev \
      ffmpeg \
      aria2 \
      python3-pip \
      build-essential \
      ca-certificates \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . /app/

CMD ["python3", "main.py"]


