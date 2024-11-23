# Use Python slim as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY Pipfile Pipfile.lock ./
COPY .env /app/.env

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install pipenv and dependencies
RUN pip install --no-cache-dir pipenv && \
    pipenv install --system --deploy

# Copy the rest of the application files
COPY . .

# Expose the application port
EXPOSE 8000

# Set environment variables
ENV FLASK_ENV=production

# Run the application
CMD ["python", "app.py"]