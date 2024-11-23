# Use Python slim base image
FROM python:3.10-slim

# Install dependencies for ffmpeg and other system requirements
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    swig \
    portaudio19-dev \
    libpulse-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files, including the web-app/uploads folder
COPY . .

# Set environment variables for the application
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/service_account.json"

# Ensure the uploads directory exists and set permissions
RUN mkdir -p /web-app/uploads && chmod -R 777 /web-app/uploads

# Expose port 8000 for Flask
EXPOSE 8000

# Default command to run the application
CMD ["python3", "app.py"]
