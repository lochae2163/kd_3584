FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose is optional (mostly for documentation)
EXPOSE 8000

# Use shell form OR exec form with sh -c to allow environment variable expansion
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]