FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Фиктивный порт для Timeweb
EXPOSE 8000

CMD ["python", "bot_with_chatid.py"]
