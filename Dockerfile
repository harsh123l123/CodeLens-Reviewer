FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose server port
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

# Start CodeLens server
CMD ["python", "backend/server.py"]
