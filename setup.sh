#!/bin/bash

# Exit on failure
set -e

# Python virtual environment
if [ ! -d "venv" ]; then
    echo "Setting up python virtual environment..."
    python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create a .env for credentials
echo "Creating .env file with credentials..."
read -p "Enter MinIO username (default: minioadmin): " username
username=${username:-minioadmin}
read -sp "Enter MinIO password (default minioadmin): " password
echo ""
password=${password:-minioadmin}
echo "MINIO_ROOT_USER=$username" > .env
echo "MINIO_ROOT_PASSWORD=$password" >> .env

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running!"
    exit 1
fi
# Start MinIO server
# For a specific storing path, can add: -v ASBOLUTE_PATH:/weather-data-bucket, before the env line
echo "Starting MinIO container..."
docker run -d \
    --name minio \
    -p 9000:9000 \
    -p 9001:9001 \
    --env-file .env \
    quay.io/minio/minio server /weather-data-bucket --console-address ":9001"

echo ""
echo "Setup complete!"
echo "Access MinIO console at: http://localhost:9001"
echo ""
echo "To run the pipeline:"
echo "  python3 -m src.orchestration.pipeline"
echo ""
echo "Note: By default, only 1 day is ingested"
echo "Check src/config/settings.py (line 31) to modify DAYS_TO_INGEST."
