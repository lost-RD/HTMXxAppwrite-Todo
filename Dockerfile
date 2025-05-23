# Use a specific digest for better reproducibility
FROM python:3.10.13-bullseye

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make sure Flask runs in production mode
ENV FLASK_APP=main.py
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Run the application with explicit host binding
CMD ["python", "-u", "main.py"] 