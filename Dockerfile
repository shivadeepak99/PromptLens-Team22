FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set work directory
WORKDIR /app_root

# Install system dependencies (required for psycopg2 and ml libraries if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app_root/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the actual application code
COPY ./app /app_root/app
COPY ./ml_service /app_root/ml_service
# We must copy .env so it can easily see the Neon connection if not passed manually, 
# but passing as a Render env variable is better practice.
COPY .env /app_root/.env

# Default port exposure
EXPOSE 8000

# Run the FastAPI server
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
