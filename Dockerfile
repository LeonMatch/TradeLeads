# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application with flexible port binding
CMD exec gunicorn --bind :$PORT app:app --workers 1 --threads 8 --timeout 0 --access-logfile - --error-logfile -
