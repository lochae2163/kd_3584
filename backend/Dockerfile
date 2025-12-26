FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose is optional (mostly for documentation)
EXPOSE 8000

# Use Python to run - this will use your __main__ block
CMD ["python", "-m", "app.main"]