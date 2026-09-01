#!/bin/sh
set -e

cd /app/backend

echo "Starting FinPilot FastAPI backend..."
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/fastapi.log 2>&1 &

cd /app/frontend

echo "Starting FinPilot Next.js frontend..."
npm run start -- -H 127.0.0.1 -p 3000 > /tmp/next.log 2>&1 &

echo "Starting Nginx on Hugging Face port 7860..."
exec nginx -g "daemon off;"
