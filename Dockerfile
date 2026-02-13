FROM python:3.11-slim

WORKDIR /app

# install system dependencies required for python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

COPY . .

CMD ["uvicorn", "app.main:app", "--host", 0.0.0.0 "--port", "8080"]
