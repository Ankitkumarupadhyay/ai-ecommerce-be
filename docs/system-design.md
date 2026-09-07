# System Design & Production Architecture - Backend

## Overview

The **Mini AI E-Commerce Application Backend** is built using FastAPI (Python async) and MongoDB Atlas, deployed on **Vercel Serverless**. It implements strict security boundaries, price snapshot calculation, role-based access control (RBAC), Stripe webhook payment verification, and real-data AI tool execution with full audit logging and IP Geolocation enrichment.

---

## High-Level System Architecture

```
User (Browser / Client)
       │
       ▼
Netlify Edge CDN (Frontend SPA)
       │
       ▼ HTTP REST / Bearer JWT
Vercel Serverless Network (FastAPI Backend)
       │
       ├── MongoDB Atlas (Async Motor Connection: users, products, carts, orders, webhook_events, ai_chat_logs)
       │
       ├── External Integrations:
       │     ├── Google OAuth2 (ID Token Verification)
       │     ├── Stripe API & Webhooks (Checkout Sessions & Signature Validation)
       │     ├── IP Geolocation (ip-api.com lookup for country & city logging)
       │     └── OpenAI API / LangChain Agent (Authorized Backend Data Tools)
```

---

## Scalability Strategy

### 1. API Layer
* **Vercel Serverless Infrastructure**: Automatic execution scaling without manual server management.
* **Asynchronous I/O**: Asynchronous route handlers and Motor database driver prevent thread blocking.

### 2. Database Layer
* **MongoDB Atlas**: Managed cloud database deployment with replica sets and secondary read preference for search/catalog queries.

### 3. AI Agent Infrastructure
* **Semantic Caching**: Cache frequent store query answers using Redis/Upstash.
* **Token Streaming & Rate-Limiting**: Stream tokens via SSE and protect agent endpoints with token bucket rate limiters.
