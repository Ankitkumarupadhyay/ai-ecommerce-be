# One-Page System Design & Architecture - Backend

## 📌 Deliverables & Project Summary

| Deliverable | Details / Link |
| :--- | :--- |
| **Live Frontend URL** | [https://ai-e-com.netlify.app](https://ai-e-com.netlify.app) |
| **Live Backend API** | [https://ai-ecommerce-be.vercel.app](https://ai-ecommerce-be.vercel.app) |
| **API Swagger Documentation** | [https://ai-ecommerce-be.vercel.app/docs](https://ai-ecommerce-be.vercel.app/docs) |
| **GitHub Repository** | [https://github.com/Ankit0090/AI-E-Commerce](https://github.com/Ankit0090/AI-E-Commerce) |
| **Database Schema** | [docs/database-schema.md](file:///Users/ankit/Projects/Moksha%20Media/AI%20E-Commerce/backend/docs/database-schema.md) |
| **API Documentation** | [docs/api-documentation.md](file:///Users/ankit/Projects/Moksha%20Media/AI%20E-Commerce/backend/docs/api-documentation.md) |
| **Total Time Taken** | `4 Hours` |
| **AI Tools Used** | `Gemini 3.6 Flash (Antigravity AI Coding Assistant)`, `OpenAI GPT-4o-mini`, `LangChain / LangGraph` |

---

## 🏗️ 1. Core Architecture Overview

The application is structured into six core components:

1. **Frontend (Client Layer)**: React 19 Single Page Application built with TypeScript, Vite, Redux Toolkit, TanStack Query, and Tailwind CSS. Deployed on **Netlify**.
2. **FastAPI Backend (API Layer)**: Async Python REST API framework providing fast, non-blocking asynchronous request handling with Pydantic schema validation. Deployed on **Vercel Serverless**.
3. **Database (Persistence Layer)**: MongoDB Atlas storing entity collections for `users`, `products`, `carts`, `orders`, `webhook_events`, and `ai_chat_logs`.
4. **AI Support Agent**: LangChain / LangGraph agent powered by OpenAI GPT-4o-mini. Equipped with secure backend tools (`get_available_products`, `search_products`, `get_my_orders`) and IP Geolocation audit logging (`ip-api.com`).
5. **Google Authentication**: OAuth2 ID token verification endpoint on the backend issuing signed, stateless JWT access tokens for session management and RBAC.
6. **Stripe Integration**: Stripe Checkout Sessions with server-side price snapshot validation and cryptographically signed Stripe Webhook processing (`checkout.session.completed`) with idempotency tracking.

---

## 📐 2. System Architecture Diagram

```mermaid
graph TD
    User["🌐 User (Browser / Mobile Client)"]
    
    subgraph FrontendApp["Frontend Layer (Netlify Edge CDN)"]
        SPA["React 19 SPA (Vite + Redux Toolkit + TanStack Query)"]
    end
    
    subgraph BackendApp["Backend API Layer (Vercel Serverless FastAPI)"]
        FastAPI["FastAPI Async REST API"]
        JWTAuth["JWT Authentication & RBAC Guard"]
        StripeHandler["Stripe Webhook & Payment Handler"]
        AIEngine["LangChain / LangGraph AI Agent Engine"]
    end

    subgraph DatabaseLayer["Database Layer (MongoDB Atlas Cluster)"]
        MongoDB[("MongoDB Atlas Database\n(users, products, carts, orders,\nwebhook_events, ai_chat_logs)")]
    end

    subgraph ExternalServices["Third-Party Integrations"]
        GoogleOAuth["🔐 Google OAuth2 Service"]
        StripeAPI["💳 Stripe API & Webhooks"]
        OpenAI["🤖 OpenAI API (GPT-4o-mini)"]
        GeoIP["📍 IP Geolocation API (ip-api.com)"]
    end

    User -->|HTTPS| SPA
    SPA -->|1. Sign-In ID Token| FastAPI
    FastAPI -->|2. Verify ID Token| GoogleOAuth
    FastAPI -->|3. Issue JWT Token| SPA
    
    SPA -->|4. Browse / Cart / Orders (Bearer JWT)| JWTAuth
    JWTAuth -->|5. Async Query / Mutate| MongoDB

    SPA -->|6. Initiate Checkout| StripeHandler
    StripeHandler -->|7. Create Checkout Session| StripeAPI
    StripeAPI -->|8. Webhook Event Notification| StripeHandler
    StripeHandler -->|9. Idempotent Deduct Stock & Update Status| MongoDB

    SPA -->|10. AI Chat Request| AIEngine
    AIEngine -->|11. Prompt Guardrails & User Context| OpenAI
    AIEngine <-->|12. Execute DB Tools (products, orders)| MongoDB
    FastAPI -->|13. Enrich IP with City & Country| GeoIP
    FastAPI -->|14. Log Chat Interaction| MongoDB
    FastAPI -->|15. Formatted Markdown Response| SPA
```

---

## ☁️ 3. Production Deployment Approach (Netlify + Vercel)

```
                               ┌──────────────────────────────────────────────────┐
                               │                 User Web Browser                 │
                               └────────────────────────┬─────────────────────────┘
                                                        │
                      ┌─────────────────────────────────┴─────────────────────────────────┐
                      │                                                                   │
                      ▼                                                                   ▼
       ┌───────────────────────────────┐                                   ┌───────────────────────────────┐
       │ Netlify Edge CDN              │                                   │ Vercel Serverless Network     │
       │ (Frontend Static SPA Build)   │                                   │ (FastAPI Python Runtime)      │
       └───────────────────────────────┘                                   └──────────────┬────────────────┘
                                                                                          │
                                                                                          ▼
                                                                           ┌───────────────────────────────┐
                                                                           │ MongoDB Atlas                 │
                                                                           │ (Cloud Database Cluster)      │
                                                                           └───────────────────────────────┘
```

* **Frontend Deployment (Netlify)**:
  - Deployed on **Netlify** with global edge CDN distribution.
  - Configured with `netlify.toml` for Single Page Application (SPA) fallback routing.
  - Automatic SSL certificate provision and instant build previews.
* **Backend Deployment (Vercel)**:
  - Deployed on **Vercel** as a serverless Python FastAPI application.
  - Automatic scaling across Vercel serverless edge infrastructure with sub-second cold starts and global routing.
  - Managed environment variables for sensitive API keys (`OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, `JWT_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `MONGODB_URI`).
* **Database Deployment (MongoDB Atlas)**:
  - **MongoDB Atlas** managed multi-AZ cloud deployment with automated replica sets, encrypted storage, and automated failover.

---

## 🚀 4. How to Scale Backend Strategy (Vercel & Cloud Infrastructure)

When traffic and AI request volumes increase significantly (e.g., from 1K to 100K+ daily active users), the backend scales using the following strategy:

### A. Scaling the FastAPI Serverless Backend (Vercel)
1. **Serverless Auto-Scaling**: Vercel automatically scales function execution concurrency in response to spikes in HTTP traffic without manual server provisioning or load balancer management.
2. **Asynchronous I/O Execution**: FastAPI utilizes Python `async/await` and Motor async driver. Non-blocking network I/O allows each serverless instance to handle multiple concurrent asynchronous queries efficiently.
3. **Stateless Bearer JWT Authentication**: User authorization is verified statelessly via signed JWTs in HTTP headers, eliminating server-side session lookup bottlenecks.

### B. Scaling Database Operations (MongoDB Atlas)
1. **Connection Pooling & Auto-Scaling**: Configure Motor MongoDB driver connection pooling per serverless worker and leverage MongoDB Atlas Auto-Scaling (M10+ clusters) for dynamic RAM/Storage allocation.
2. **Read/Write Segregation**: Direct heavy product catalog queries to MongoDB secondary read replicas using `ReadPreference.SECONDARY_PREFERRED`.
3. **Compound Database Indexing**: Ensure strict indexing on frequent query targets:
   - `users.email` (Unique) & `users.google_id` (Unique)
   - `carts.user_id` (Unique)
   - `orders.user_id` & `orders.stripe_checkout_session_id`
   - `webhook_events.event_id` (Unique)
   - `ai_chat_logs.session_id` & `ai_chat_logs.created_at`

### C. Scaling the AI Agent & LLM Infrastructure
1. **Semantic Response Caching (Upstash Redis / Redis Cloud)**: Store embeddings or exact hash keys of common customer support questions (e.g., shipping policies, stock availability). Subsequent identical queries return instant cached answers without incurring LLM API latency or cost.
2. **Token Streaming (Server-Sent Events)**: Stream LLM response tokens directly to the client as they are generated to deliver instant initial response feedback and prevent request timeout.
3. **Token Rate-Limiting & Quotas**: Implement token bucket rate limiters per IP / user tier to prevent API abuse and control costs during usage spikes.

### D. Scaling Payment & Webhook Processing
1. **Idempotent Webhook Execution**: `/api/v1/payments/webhook` verifies raw `Stripe-Signature` headers and records every processed `event_id` into the `webhook_events` collection before stock reduction or status mutation, ensuring safe retries under high load.
