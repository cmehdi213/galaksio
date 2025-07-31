# Galaksio Docker Deployment

This directory contains Docker-related documentation for deploying Galaksio 2.

## 🚀 Quick Start

The main Docker configuration files are located in the **root directory**:

- [`Dockerfile`](../Dockerfile) - Multi-stage build for optimized production deployment
- [`docker-compose.yml`](../docker-compose.yml) - Complete stack with optional services

## 📦 Building and Running

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/cmehdi213/galaksio.git
cd galaksio

# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop all services
docker-compose down
