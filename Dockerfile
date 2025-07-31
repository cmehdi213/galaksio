# Galaksio 2 - Modern Galaxy Workflow Interface
# Dockerfile for Galaxy 25.0 compatibility
# Multi-stage build for optimized image size and security

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    apache2 \
    libapache2-mod-wsgi-py3 \
    && rm -rf /var/lib/apt/lists/* && \
    a2enmod wsgi && \
    a2enmod rewrite && \
    a2enmod headers

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application user
RUN useradd --create-home --shell /bin/bash galaksio && \
    mkdir -p /app && \
    chown -R galaksio:galaksio /app

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=galaksio:galaksio . .

# Install application in development mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/server/conf /app/server/log && \
    chown -R galaksio:galaksio /app/server/conf /app/server/log

# Copy Apache configuration
COPY docker/apache.conf /etc/apache2/sites-available/000-default.conf

# Configure Apache
RUN sed -i 's/Listen 80/Listen 8081/g' /etc/apache2/ports.conf && \
    sed -i 's/VirtualHost \*:80/VirtualHost *:8081/g' /etc/apache2/sites-available/000-default.conf

# Create startup script
COPY docker/startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/ || exit 1

# Switch to non-root user
USER galaksio

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/startup.sh"]

# Default command
CMD ["--start"]
