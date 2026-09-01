FROM node:20-bookworm

# Python + Nginx for the FastAPI backend, Next.js frontend and single public port.
RUN apt-get update && \
    apt-get install -y python3 python3-pip nginx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------- Backend ----------------
COPY backend /app/backend
RUN python3 -m pip install --break-system-packages --no-cache-dir \
    fastapi "uvicorn[standard]" pydantic pydantic-settings sqlalchemy \
    python-dotenv pandas numpy httpx python-multipart \
    PyMuPDF sentence-transformers chromadb

# ---------------- Frontend ----------------
COPY frontend /app/frontend
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# ---------------- Proxy / startup ----------------
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 7860

CMD ["/app/start.sh"]
