# Database Schema Documentation - MongoDB

Database Name: `mini_ai_ecommerce`

The application uses MongoDB for storing entity data and maintains indexing for performance and uniqueness constraints.

---

## 1. `users` Collection

Stores user identity and Role-Based Access Control (RBAC) definitions.

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Default Primary Index |
| `google_id` | String | Unique Google OAuth Sub Identifier | Unique Index |
| `email` | String | User Email Address | Unique Index |
| `name` | String | Display Name | None |
| `picture` | String | Avatar URL | None |
| `role` | String | `customer` or `admin` (Default: `customer`) | None |
| `created_at` | DateTime | Timestamp of creation | None |
| `updated_at` | DateTime | Timestamp of last modification | None |

---

## 2. `products` Collection

Stores store inventory and item catalog details.

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Default Primary Index |
| `name` | String | Product Name | Text / Keyword Search |
| `description` | String | Detailed product copy | None |
| `price` | Double | Unit price in USD (> 0) | None |
| `currency` | String | Currency code (Default: `usd`) | None |
| `image_url` | String | Asset URL | None |
| `stock` | Integer | Units available in inventory (>= 0) | None |
| `category` | String | `Electronics`, `Clothing`, `Accessories`, `Home` | ASCENDING Index |
| `is_active` | Boolean | Visibility flag | ASCENDING Index |
| `created_at` | DateTime | Creation timestamp | None |
| `updated_at` | DateTime | Modification timestamp | None |

---

## 3. `carts` Collection

Maintains real-time active shopping carts for authenticated users (1 cart per user).

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Default Primary Index |
| `user_id` | String | Foreign Key referencing `users._id` | Unique Index |
| `items` | Array[Object] | List of cart items: `[{ product_id, quantity }]` | None |
| `updated_at` | DateTime | Last updated timestamp | None |

---

## 4. `orders` Collection

Stores customer purchases with price and product name snapshots.

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Default Primary Index |
| `user_id` | String | Foreign Key referencing `users._id` | ASCENDING Index |
| `items` | Array[Object] | Price snapshot items: `[{ product_id, product_name, price, quantity }]` | None |
| `subtotal` | Double | Order subtotal before tax | None |
| `total` | Double | Final total in USD | None |
| `currency` | String | Currency code (`usd`) | None |
| `payment_status` | String | `pending`, `paid`, `failed`, `cancelled` | None |
| `order_status` | String | `pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled` | None |
| `stripe_checkout_session_id` | String | Stripe Checkout Session ID | ASCENDING (Sparse) |
| `stripe_payment_intent_id` | String | Stripe Payment Intent ID | None |
| `created_at` | DateTime | Placed timestamp | None |
| `updated_at` | DateTime | Modification timestamp | None |

---

## 5. `webhook_events` Collection

Audit log ensuring idempotent processing of incoming Stripe Webhook retries.

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Default Primary Index |
| `event_id` | String | Stripe Event ID | Unique Index |
| `type` | String | Webhook event type | None |
| `processed_at` | DateTime | Processing timestamp | None |

---

## 6. `ai_chat_logs` Collection

Logs every interaction with the AI Support Agent for analytics, audit, and user rate-limiting.

| Field | Type | Description | Index |
| :--- | :--- | :--- | :--- |
| `_id` | ObjectId | Primary Key | Default Primary Index |
| `session_id` | String | Chat session identifier | ASCENDING Index |
| `user_id` | String | User ID (if authenticated) | ASCENDING (Sparse) Index |
| `is_authenticated` | Boolean | Authentication status flag | None |
| `question` | String | User message / query | None |
| `response` | String | AI agent generated response | None |
| `tools_used` | Array[String] | LangChain tools executed (e.g., `get_available_products`) | None |
| `ip_address` | String | Client IP address | None |
| `country` | String | Resolved country via IP Geolocation | None |
| `city` | String | Resolved city via IP Geolocation | None |
| `browser` | String | Parsed browser family and version | None |
| `os` | String | Parsed operating system | None |
| `device` | String | `Desktop`, `Mobile`, or `Tablet` | None |
| `created_at` | DateTime | Interaction timestamp | ASCENDING Index |
