# Use slim Python image to keep container size small
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run injects PORT env variable — uvicorn must bind to it
ENV PORT=8080

# Run the app
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
