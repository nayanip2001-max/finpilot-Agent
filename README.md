# 🕷️ FinPilot AI

### Your Friendly Neighborhood Investment Copilot

FinPilot AI is an **explainable, risk-aware multi-agent investment research system** that personalizes recommendations using the investor's risk profile, portfolio exposure, market signals, sentiment, and available financial evidence.

> **Core idea:** Don't just ask *"Is this stock good?"* — ask *"Is it right for this investor?"*

---
## 🕷️ Live Demo

🔴 **[Launch FinPilot AI →](https://finpilot-vercel-git-main-de-buggers.vercel.app/)**

Experience the Spider-Man-inspired AI investment dashboard,
multi-agent analysis, RAG evidence, risk reasoning and
decision trace.

> ⚠️ Hackathon demo — uses synthetic data.
---

## 🚀 Architecture

```text
Frontend (Next.js / React)
          │
          ▼
      FastAPI
          │
          ▼
    Orchestrator
          │
 ┌────────┼────────┐
 ▼        ▼        ▼
Technical Fundamental Sentiment
 Agent     /RAG      Agent
 └────────┼────────┘
          ▼
      Risk Agent
          │
          ▼
   Synthesis Agent
          │
    ┌─────┴─────┐
    ▼           ▼
Recommendation Explanation
```

### Agents

- **Technical Agent** — analyzes OHLCV, momentum, trends and volume.
- **Fundamental/RAG Agent** — retrieves documentary evidence and produces evidence-backed fundamental signals.
- **Sentiment Agent** — analyzes demonstration news/sentiment data.
- **Risk Agent** — evaluates investor risk profile, portfolio exposure and concentration.
- **Synthesis Agent** — combines all signals into `BUY / HOLD / REDUCE / AVOID` using auditable decision logic.

---

## 🚨 RAG Dataset, Not MCP

**MCP is NOT used for the current MVP.**

The financial research documents are stored locally and processed through a RAG pipeline:

```text
PDFs → Text Extraction → Chunking → Embeddings → ChromaDB → Retrieval → Fundamental Agent
```

The current prototype uses a **small synthetic/local RAG dataset** so the demo is reproducible, offline-friendly and independent of paid external data APIs.

### Why not MCP?

MCP is useful for connecting agents to external tools and live sources. For this hackathon, adding MCP would introduce unnecessary infrastructure without improving the core demonstration.

**Future:** MCP can later connect live market APIs, news, filings, brokerage/portfolio data and other external tools.

---

## 📚 Demo Dataset

### Synthetic Market Data

OHLCV data is generated for:

| Symbol | Company |
|---|---|
| RELIANCE | Reliance Industries |
| TCS | Tata Consultancy Services |
| HDFCBANK | HDFC Bank |
| INFY | Infosys |
| ICICIBANK | ICICI Bank |

Approximately **260 weekday observations per symbol** are included.

> ⚠️ These prices are synthetic and are **not real historical market data**.

### Synthetic RAG Documents

```text
backend/data/documents/

reliance/
├── annual_report.pdf
└── q4_results.pdf

tcs/
└── q4_results.pdf
```

The documents simulate annual reports, quarterly results, business highlights, outlook and risk factors.

`HDFCBANK`, `INFY`, and `ICICIBANK` intentionally have no financial PDFs. This enables the **degraded-data demonstration**.

---

## 🛡️ Graceful Degradation

FinPilot is designed to **know when it doesn't have enough evidence**.

```text
No RAG documents
      ↓
Fundamental Agent = UNKNOWN / DEGRADED
      ↓
Confidence reduced
      ↓
Synthesis accounts for missing evidence
      ↓
No fabricated financial claims
```

This prevents the system from inventing financial evidence when documents are unavailable.

---

## 🧠 Personalized Decision Making

A bullish stock does not automatically mean **BUY**.

Example:

```text
Technical      → BULLISH
Sentiment      → POSITIVE
Fundamental    → POSITIVE
Risk           → OVER_CONCENTRATED
                     ↓
                   HOLD
```

The Risk Agent can therefore override market enthusiasm when the investor already has excessive exposure.

The same stock and question can produce different recommendations for different investor profiles.

---

## 🔍 Reasoning Trace

FinPilot exposes a concise, **user-facing decision trace** rather than hidden chain-of-thought:

```text
User Profile   → CONSERVATIVE
Technical      → BULLISH (79%)
Fundamental    → DEGRADED
Sentiment      → POSITIVE (64%)
Risk           → OVER_CONCENTRATED (82%)
Synthesis      → HOLD (45%)
```

This makes the recommendation auditable and understandable.

---

## 📊 Metrics

The metrics layer provides observability into analysis runs and agents.

Tracked concepts include:

- analysis run ID
- user and symbol
- latency
- recommendation
- confidence
- agent signals
- agent status
- signal conflicts
- degraded-data state
- portfolio concentration
- risks and decision factors

The Metrics page turns the multi-agent system from a black box into an observable pipeline.

---

## 🕷️ Spider-Man Inspired Frontend

The UI is designed around a **Spider-Man-inspired AI HUD**.

| Theme | FinPilot Concept |
|---|---|
| 🕷️ Spider-Sense | Signal/risk detection |
| 🕸️ Web | Connected multi-agent architecture |
| 🖥️ Suit HUD | Investor dashboard |
| ⚠️ Threat detection | Portfolio concentration & risk |
| 🎯 Mission result | Final recommendation |

The frontend uses a dark, high-contrast HUD aesthetic with agent cards, confidence indicators, charts, risk alerts and decision traces.

### Frontend Stack

- Next.js / React
- Tailwind CSS
- Recharts
- shadcn/ui

---

## ⚙️ Backend Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite for MVP
- ChromaDB for RAG
- NumPy / Pandas for market analysis

### Database Concepts

```text
users
profiles
portfolios
watchlists
agent_runs
signals
recommendations
performance_metrics
```

SQLite can be replaced with PostgreSQL/Supabase for production.

---

## 🤖 LLM Layer

The LLM is separated from the deterministic decision engine:

```text
Agent Outputs
     ↓
Deterministic Synthesis
     ↓
BUY / HOLD / REDUCE / AVOID
     ↓
LLM Narration
     ↓
Human-readable explanation
```

The MVP currently supports:

```text
LLM_MODE=mock
```

so the complete pipeline can run without an external LLM API key.

A real LLM provider can be connected through the existing `call_llm()` abstraction.

---

## 📁 Project Structure

```text
finpilot-ai/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── rag/
│   │   ├── market/
│   │   ├── portfolio/
│   │   ├── users/
│   │   ├── metrics/
│   │   ├── database/
│   │   └── utils/
│   └── data/
│       ├── market/
│       ├── documents/
│       └── users/
│
├── frontend/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── hooks/
│       ├── lib/
│       └── types/
│
└── docs/
```

---

## 🧪 Demo Scenarios

### 1. Personalized Recommendation

Ask the same question for two different investors:

> **"Should I increase my RELIANCE position?"**

Demonstrates that investor context changes the recommendation.

### 2. Concentration Risk

```text
Bullish Market Signals
        +
Over-Concentrated Portfolio
        ↓
      HOLD
```

### 3. Degraded Data

Select `INFY` and demonstrate:

```text
No financial documents
        ↓
Fundamental Agent degraded
        ↓
No fabricated evidence
```

### 4. Explainability

Show:

- agent consensus
- confidence
- reasons
- risks
- evidence
- reasoning trace
- what would change the decision

---

## ⚠️ Assumptions & Limitations

- This is a hackathon/demo system, not a brokerage platform.
- Market, investor and document datasets are synthetic.
- The system does not execute trades.
- Confidence is not a guarantee of correctness.
- Missing evidence is explicitly treated as degraded data.
- SQLite and ChromaDB are sufficient for the MVP.
- Production deployment would require validated live data, authentication, security, audit controls, model evaluation and regulatory review.
- MCP is optional and intentionally not used for the current local RAG dataset.

---

## 🔐 Disclaimer

**FinPilot AI is a hackathon prototype and is not financial advice.**

Synthetic data and simulated documents are used for demonstration purposes only. Recommendations should not be used to make real investment decisions.

---

# 🕷️ FinPilot AI

> **Don't just predict the market. Understand the investor.**

> **Don't fabricate evidence. Admit when it is missing.**

> **Don't hide the decision. Explain it.**

### With great financial AI comes great responsibility. 🕸️
>>>>>>> origin/main
