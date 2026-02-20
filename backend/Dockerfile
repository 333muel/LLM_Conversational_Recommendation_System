FROM python:3.12.3-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Move data and checkpoints from parent directory if needed
# But docker build context only sees ./backend/
# So we might need to mount these as volumes or copy them in during build

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
