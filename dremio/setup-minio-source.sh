#!/bin/bash
# Setup Dremio with MinIO Gold Layer access
# Run this after completing Dremio's initial setup wizard

DREMIO_URL="http://localhost:9047"
DREMIO_USER="${DREMIO_USER:-admin}"
DREMIO_PASS="${DREMIO_PASS:-admin123}"

echo "=== Dremio MinIO Gold Layer Setup ==="
echo ""

# Login to Dremio
echo "Logging in to Dremio..."
LOGIN_RESPONSE=$(curl -s -X POST "${DREMIO_URL}/apiv2/login" \
  -H "Content-Type: application/json" \
  -d "{\"userName\": \"${DREMIO_USER}\", \"password\": \"${DREMIO_PASS}\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "Failed to login. Please check credentials."
  echo "Response: $LOGIN_RESPONSE"
  echo ""
  echo "Make sure you've completed Dremio's initial setup at ${DREMIO_URL}"
  echo "Then set DREMIO_USER and DREMIO_PASS environment variables."
  exit 1
fi

echo "Login successful!"

# Create MinIO Gold source
echo "Creating MinIO Gold Layer source..."
SOURCE_RESPONSE=$(curl -s -X POST "${DREMIO_URL}/api/v3/catalog" \
  -H "Authorization: _dremio${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "entityType": "source",
    "name": "MinIO-Gold",
    "type": "S3",
    "config": {
      "credentialType": "ACCESS_KEY",
      "accessKey": "minioadmin",
      "accessSecret": "minioadmin123",
      "secure": false,
      "externalBucketList": ["gold"],
      "enableAsync": true,
      "compatibilityMode": true,
      "requesterPays": false,
      "enableFileStatusCheck": true,
      "rootPath": "/gold",
      "propertyList": [
        {"name": "fs.s3a.endpoint", "value": "minio:9000"},
        {"name": "fs.s3a.path.style.access", "value": "true"},
        {"name": "dremio.s3.compat", "value": "true"}
      ]
    }
  }')

if echo "$SOURCE_RESPONSE" | grep -q '"entityType":"source"'; then
  echo "MinIO Gold source created successfully!"
else
  echo "Source creation response: $SOURCE_RESPONSE"
  if echo "$SOURCE_RESPONSE" | grep -q "already exists"; then
    echo "Source already exists - that's OK!"
  fi
fi

echo ""
echo "=== Setup Complete ==="
echo "You can now access the Gold layer data in Dremio under 'MinIO-Gold' source."
echo ""
