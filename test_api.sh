#!/bin/bash

source .env
BASE_URL="http://localhost:8000"

echo "1. Создание платежа..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/payments" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: test-$(date +%s)" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.50,
    "currency": "USD",
    "description": "Test payment",
    "webhook_url": "https://webhook.site/xxx"
  }')

echo "Response: $RESPONSE"

PAYMENT_ID=$(echo $RESPONSE | grep -o '"payment_id":"[^"]*' | cut -d'"' -f4)

if [ -n "$PAYMENT_ID" ]; then
  echo -e "\n2. Получение информации о платеже..."
  curl -s -X GET "$BASE_URL/api/v1/payments/$PAYMENT_ID" \
    -H "X-API-Key: $API_KEY" | jq '.'
else
  echo "Failed to get payment_id"
fi
