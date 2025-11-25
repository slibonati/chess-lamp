FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY chess_lamp.py .
COPY govee_lan.py .
COPY config.json.example .

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run the application with unbuffered output for logs
CMD ["python3", "-u", "chess_lamp.py"]

