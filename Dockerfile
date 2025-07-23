FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    chromium \
    chromium-driver \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Переменные окружения для headless Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

EXPOSE 8000

CMD ["uvicorn", "gosconnect.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
