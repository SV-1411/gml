#!/bin/bash
# Start MinIO Docker Container

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Starting MinIO..."
docker-compose -f docker-compose.dev.yml up -d minio

echo ""
echo "Waiting for MinIO to start..."
sleep 5

echo ""
echo "MinIO should be available at:"
echo "  Console: http://localhost:9001"
echo "  API: http://localhost:9000"
echo ""
echo "Default credentials:"
echo "  Username: minioadmin"
echo "  Password: minioadmin"
echo ""

