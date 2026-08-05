FROM python:3.11-slim

WORKDIR /app
# alembic/uvicorn chạy qua console script -> sys.path[0] là /usr/local/bin, không phải cwd.
# Không có dòng này thì `from persistence.models import Base` trong migrations/env.py fail.
ENV PYTHONPATH=/app
COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && git config --global --add safe.directory /repo
COPY . .

EXPOSE 8810
