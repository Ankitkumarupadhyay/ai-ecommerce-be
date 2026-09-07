# API Documentation - Mini AI E-Commerce API

Base URL: `http://localhost:8000/api/v1` (Production: `https://ai-ecommerce-be.vercel.app/api/v1`)  
Swagger Interactive UI: `http://localhost:8000/docs` (Production: `https://ai-ecommerce-be.vercel.app/docs`)

---

## 1. Authentication

### POST `/auth/google`
Authenticates Google OAuth credential ID token, registers new users (default role: `customer`), or retrieves existing users, and issues a JWT access token.

* **Auth Required**: None
* **Request Body**:
  ```json
  {
    "credential": "google_id_token_string"
  }
  ```
* **Response Example (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "token_type": "bearer",
    "user": {
      "id": "65f01234567890abcdef2222",
      "email": "customer@example.com",
      "name": "Jane Doe",
      "picture": "https://lh3.googleusercontent.com/a/...",
      "role": "customer"
    }
  }
  ```

### GET `/auth/me`
Retrieves the currently authenticated user's profile details.

* **Auth Required**: Bearer JWT
* **Response Example (200 OK)**:
  ```json
  {
    "id": "65f01234567890abcdef2222",
    "email": "customer@example.com",
    "name": "Jane Doe",
    "picture": "https://lh3.googleusercontent.com/a/...",
    "role": "customer"
  }
  ```

---

## 2. Products

### GET `/products`
Returns listing of active products with optional search query and category filtering.

* **Auth Required**: None
* **Query Parameters**:
  * `search` (optional): Filter by product name, description, or category keyword.
  * `category` (optional): Filter by exact category (e.g. `Electronics`, `Clothing`, `Accessories`, `Home`).
* **Response Example (200 OK)**:
  ```json
  [
    {
      "id": "65f01234567890abcdef3333",
      "name": "Wireless Noise-Canceling Headphones",
      "description": "Premium over-ear wireless headphones with active noise cancellation...",
      "price": 249.99,
      "currency": "usd",
      "image_url": "https://images.unsplash.com/photo-1505740420928...",
      "stock": 25,
      "category": "Electronics",
      "is_active": true,
      "created_at": "2026-09-05T12:00:00Z",
      "updated_at": "2026-09-05T12:00:00Z"
    }
  ]
  ```

### GET `/products/{product_id}`
Returns details for a specific product by ID.

* **Auth Required**: None

---

## 3. Cart Management

### GET `/cart`
Returns the user's active shopping cart with line item totals.

* **Auth Required**: Bearer JWT (Customer)

### POST `/cart/items`
Adds an item to the shopping cart or increments quantity after verifying available stock.

* **Auth Required**: Bearer JWT (Customer)

### PUT `/cart/items/{product_id}`
Updates quantity for an existing cart item.

* **Auth Required**: Bearer JWT (Customer)

### DELETE `/cart/items/{product_id}`
Removes a product from the active cart.

* **Auth Required**: Bearer JWT (Customer)

---

## 4. Order Management

### POST `/orders/create-from-cart`
Creates a pending order from the user's active shopping cart, snapshots product names and prices, and clears the active cart.

* **Auth Required**: Bearer JWT (Customer)

### GET `/orders`
Lists all orders belonging to the authenticated customer.

* **Auth Required**: Bearer JWT (Customer)

### GET `/orders/{order_id}`
Retrieves detailed snapshot for an order. Strictly enforces user ownership.

* **Auth Required**: Bearer JWT (Customer)

---

## 5. Payments & Webhooks

### POST `/payments/create-checkout-session`
Creates a Stripe Checkout Session for a pending order.

* **Auth Required**: Bearer JWT (Customer)

### POST `/payments/webhook`
Stripe Webhook endpoint. Converts Stripe Event object via `.to_dict()`, verifies cryptographic signature, enforces idempotency using `webhook_events`, updates `payment_status` to `paid`, `order_status` to `confirmed`, and safely reduces stock.

* **Auth Required**: None (Cryptographic Stripe-Signature header verification)

---

## 6. Admin Endpoints

* **POST `/admin/products`**: Create product (Admin)
* **PUT `/admin/products/{id}`**: Update product details/stock (Admin)
* **DELETE `/admin/products/{id}`**: Delete product (Admin)
* **GET `/admin/orders`**: View all customer orders (Admin)
* **PUT `/admin/orders/{id}/status`**: Update order status (Admin)

---

## 7. AI Support Agent

### POST `/ai/chat`
Invokes the LangChain AI agent equipped with authorized backend tools (`get_available_products`, `search_products`, `get_my_orders`). Also logs IP address, city, country, browser, OS, and device in `ai_chat_logs`.

* **Auth Required**: Optional Bearer JWT (Required for user order history queries)

### GET `/ai/logs`
Retrieves persistent AI chat interaction logs for administration and analytics.

* **Auth Required**: Bearer JWT (Admin)
