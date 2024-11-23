# Use Python slim as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements files and install dependencies
COPY requirements.txt ./
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    curl \
    git \  
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Copy environment file
COPY .env /app/.env

# Copy all project files
COPY . .

# Ensure the uploads directory exists and is writable
RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads

# Expose the application port
EXPOSE 8000

# Set default environment variables
ENV FLASK_ENV=production

# Run the Flask application
CMD ["python", "app.py"]
