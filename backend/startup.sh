#!/bin/bash
set -e

echo "Starting deployment script..."

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Start Gunicorn
echo "Starting Gunicorn..."
# Azure App Service sets the PORT environment variable. We should use it.
# We use uvicorn worker class for FastAPI.
exec gunicorn --bind=0.0.0.0:8000 --workers=4 --worker-class=uvicorn.workers.UvicornWorker src.main:app
