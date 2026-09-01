---
title: FinPilot AI
emoji: 🕷️
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
---

# 🕷️ FinPilot AI — Hugging Face Deployment

This Space runs the FinPilot AI hackathon MVP.

## Architecture

```text
Hugging Face :7860
        │
      Nginx
   ┌────┴─────┐
   ▼          ▼
Next.js     FastAPI
 :3000       :8000
              │
       SQLite / ChromaDB
       Synthetic RAG data
```

The application uses synthetic demonstration data and is not financial advice.

## Important

Do not commit API keys or `.env` files.

The current MVP can run in mock LLM mode without an external LLM API key.
