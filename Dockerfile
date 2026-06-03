# vtm - Vulnerable Task Manager
# Lab / training container. Not for production use.
#
# Single stage, python:3.12-slim. System packages cover the mysqlclient build
# (listed in requirements.txt even though the default config uses SQLite).
#
# Runtime: ./entrypoint.sh applies migrations, loads the seed fixtures on a
# fresh database, then execs `manage.py runserver 0.0.0.0:8000`.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=taskManager.settings

WORKDIR /app

# Build deps for mysqlclient (still listed in requirements.txt), curl for the
# container healthcheck, and redis-server because taskManager.settings hard-codes
# `REDIS_HOST = 'localhost'` and login uses it for failed-attempt tracking.
# Bundling Redis in the same container avoids patching upstream settings.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
        curl \
        redis-server \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Make sure the bundled entrypoint and helper scripts are executable.
RUN chmod +x /app/entrypoint.sh /app/manage.py /app/reset_db.sh /app/runapp.sh /app/start.sh 2>/dev/null || true

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
