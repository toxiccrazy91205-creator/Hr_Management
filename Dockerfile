FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS-level dependencies required by ChromaDB and document parsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project source code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/media/resumes /app/chroma_db

# Collect static files during build
RUN python manage.py collectstatic --noinput

# Expose the port
EXPOSE 8000

# Run migrations and start the server using Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn hr_agent_project.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
