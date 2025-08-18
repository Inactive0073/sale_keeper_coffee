# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Установка build-essential и зависимостей для сборки некоторых пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Устанавливаем зависимости в отдельный путь
RUN pip install --prefix=/install -r requirements.txt

# ---- Stage 2: Final image ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем только установленные пакеты
COPY --from=builder /install /usr/local

# Копируем исходники
COPY . .

# Минимизация мусора: удаляем ненужные кэши pip (по факту они уже не копируются)
# RUN rm -rf /root/.cache

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
