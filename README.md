# Backend - Mini AI E-Commerce Application

FastAPI (Python 3.9+) Asynchronous REST API providing Google OAuth2 authentication, product catalog management, cart persistence, order snapshotting, Stripe payment processing with idempotent webhooks, and an AI Support Agent powered by LangChain/LangGraph and OpenAI with IP Geolocation audit logging. Deployed on **Vercel**.

---

## 📌 Deliverables & Live Links

| Deliverable | Location / URL |
| :--- | :--- |
| **Live Backend API** | [https://ai-ecommerce-be.vercel.app](https://ai-ecommerce-be.vercel.app) |
| **Swagger Interactive Docs** | [https://ai-ecommerce-be.vercel.app/docs](https://ai-ecommerce-be.vercel.app/docs) |
| **Live Frontend App** | [https://ai-e-com.netlify.app](https://ai-e-com.netlify.app) |
| **GitHub Repository** | [https://github.com/Ankit0090/AI-E-Commerce](https://github.com/Ankit0090/AI-E-Commerce) |
| **One-Page System Design** | [SYSTEM_DESIGN.md](file:///Users/ankit/Projects/Moksha%20Media/AI%20E-Commerce/backend/SYSTEM_DESIGN.md) |
| **Database Schema** | [docs/database-schema.md](file:///Users/ankit/Projects/Moksha%20Media/AI%20E-Commerce/backend/docs/database-schema.md) |
| **API Documentation** | [docs/api-documentation.md](file:///Users/ankit/Projects/Moksha%20Media/AI%20E-Commerce/backend/docs/api-documentation.md) |
| **Total Time Taken** | `4.5 Hours` |
| **AI Tools Used** | `Gemini 3.6 Flash (Antigravity AI Coding Assistant)`, `OpenAI GPT-4o-mini`, `LangChain / LangGraph` |

---

## 🛠️ Technology Stack

* **Framework**: FastAPI (Python 3.9+) with Pydantic v2 validation and Asyncio.
* **Database Driver**: Motor (Async MongoDB Driver) connected to MongoDB Atlas.
* **Authentication**: Google OAuth2 ID token verification (`google-auth`) + HS256 JWT access tokens (`pyjwt`).
* **Payment Processing**: Stripe Python SDK with webhook signature verification & idempotency collection.
* **AI Agent & LLM**: LangChain, LangGraph, OpenAI (`gpt-4o-mini`), and custom async database tools.
* **Analytics & Geolocation**: HTTPX async IP Geolocation lookup (`ip-api.com`) and `user-agents` parser.
* **Hosting**: Vercel Serverless Functions.

---

## 📂 Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/         # API endpoints (auth, products, cart, orders, payments, admin, ai)
│   ├── core/               # App configuration, security (JWT/password), RBAC dependencies
│   ├── db/                 # MongoDB connection manager & index initialization
│   ├── models/             # PyObjectId & MongoDB entity data models
│   ├── schemas/            # Request and Response Pydantic validation schemas
│   ├── services/           # Business logic (auth, products, cart, orders, stripe, ai chat logs)
│   ├── ai/                 # LangChain agent, tool registry, prompt guardrails
│   └── main.py             # FastAPI entrypoint, middleware, CORS, route inclusion
├── docs/                   # API docs, DB schema, System design
│   ├── api-documentation.md
│   ├── database-schema.md
│   └── system-design.md
├── scripts/                # Database seed & utility scripts (seed_products.py, promote_admin.py)
├── SYSTEM_DESIGN.md        # One-page system design & deployment guide
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment template
└── .env                    # Environment variables (ignored by git)
```

---

## ✨ Core Features & Security Architecture

1. **Google OAuth2 & JWT Sessions**:
   - Accepts Google ID token from frontend `/api/v1/auth/google`.
   - Verifies signature against Google Auth public keys.
   - Registers user (default role: `customer`) and returns a signed JWT access token.
2. **Product Catalog & Management**:
   - Public product browsing with search and category filters.
   - Admin-only routes (`/api/v1/admin/products`) to create, update stock, toggle status, and delete items.
3. **Cart & Price Snapshotting**:
   - Single active cart per authenticated customer (`carts` collection).
   - Order creation snapshots item names and prices to guard against downstream catalog price modifications.
4. **Stripe Checkout & Idempotent Webhooks**:
   - Server generates Stripe Checkout Sessions (`/api/v1/payments/create-checkout-session`).
   - `/api/v1/payments/webhook` verifies raw `Stripe-Signature` headers.
   - Saves processed `event_id` into `webhook_events` collection before mutating order status to `paid` and deducting inventory, ensuring idempotency against duplicate event delivery.
5. **AI Support Agent with Audit & IP Geolocation**:
   - LangChain agent equipped with tools: `get_available_products`, `search_products`, `get_my_orders`.
   - Security Context Injection: `user_id` from JWT token is injected server-side so users cannot query orders belonging to other accounts.
   - Logs every chat interaction into `ai_chat_logs`, enriching client IP with `city` and `country` using `ip-api.com`, and parsing `browser`, `os`, and `device`.

---

## ⚡ Setup & Local Development

### 1. Prerequisites
* Python 3.9+
* MongoDB running locally (`mongodb://localhost:27017`) or MongoDB Atlas URI.

### 2. Installation Steps

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### 3. Seed Sample Products

```bash
python scripts/seed_products.py
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

FastAPI server runs at: `http://localhost:8000`  
Swagger Documentation: `http://localhost:8000/docs`

---

## 🔑 Environment Variables Reference

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name | `mini_ai_ecommerce` |
| `JWT_SECRET_KEY` | Secret key for signing JWTs | `super-secret-jwt-key` |
| `JWT_ALGORITHM` | Algorithm used for JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration time | `10080` (7 days) |
| `ALLOWED_ORIGINS` | CORS origins (comma separated) | `http://localhost:5173,https://ai-e-com.netlify.app` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `your-google-client-id.apps.googleusercontent.com` |
| `STRIPE_SECRET_KEY` | Stripe API Secret Key | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Signing Secret | `whsec_...` |
| `OPENAI_API_KEY` | OpenAI API Key for AI Agent | `sk-proj-...` |

---

## 🚀 How to Scale the Backend

When user traffic and AI request volume increase significantly, the backend scales using the following architecture:

### 1. Vercel Serverless Auto-Scaling
* **Vercel Functions**: Automatically scales request execution concurrency across global edge regions without manual load balancer management.
* **Non-Blocking Async I/O**: FastAPI with Python `async/await` and Motor driver ensures efficient execution during database & external API I/O operations.

### 2. MongoDB Atlas Database Scaling
* **Connection Pooling**: Tune Motor async driver pool settings (`maxPoolSize=100`) per serverless execution context.
* **Atlas Multi-AZ & Read Replicas**: Distribute search and product listing reads to secondary read replicas using `ReadPreference.SECONDARY_PREFERRED`.
* **Database Sharding**: Partition the `ai_chat_logs` and `orders` collections by `user_id` or `session_id` across shard keys when collection sizes exceed multi-gigabyte scale.

### 3. AI Support Agent Scaling
* **Semantic Cache**: Cache common user query answers using Redis/Upstash to return instant responses for repetitive inquiries (e.g. stock inquiries, store policies) without incurring LLM API latency or cost.
* **LLM Streaming (Server-Sent Events)**: Stream token responses to frontend to provide instantaneous UI updates and eliminate HTTP request timeouts.
* **Rate-Limiting Guards**: Enforce token bucket rate limiting per IP / User using Redis to cap costs and protect against API abuse.
