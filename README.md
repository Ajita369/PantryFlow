# 🥗 PantryFlow — AI Pantry Waste Reducer & Smart Grocery Planner

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Gemini](https://img.shields.io/badge/Gemini_AI-2.5_Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)

**PantryFlow** is a full-stack web application that helps you track kitchen inventory, get AI-powered meal suggestions based on what you already have (prioritizing items nearing expiry), generate budget-aware shopping lists, and plan your week — all with the goal of **reducing food waste**.

---

## ✨ Features

### 🔐 Authentication
- **Email-based registration and login** with JWT (access + refresh tokens)
- Auto token refresh 30 seconds before expiry
- Secure logout with refresh token blacklisting
- Protected routes with automatic redirect to login

### 📦 Pantry Management
- **Full CRUD** — add, edit, and delete pantry items
- Track name, category, quantity, unit, expiry date, purchase date, location, and notes
- **Search and filter** by name or category
- **Expiry tracking** — badges for Expired, Urgent (≤3 days), Soon (≤7 days), and OK
- **Urgency scoring** (0-100) based on expiry, quantity, and category

### 🍽️ AI Meal Suggestions
- **Gemini AI-powered** meal generation from your pantry contents
- **Deterministic scoring engine** matches pantry items to meal ingredients
- **Three-tier grouping**: Cook Today, Cook This Week, Possible Later
- **Ingredient substitution** suggestions from your existing pantry
- **AI explanations** — natural-language cooking notes for each meal
- **Smart caching** — SHA-256 hash of pantry state; regenerates only when pantry changes
- **Graceful fallback** — 5 hardcoded meal templates when AI is unavailable

### 🛒 Smart Shopping List
- **Auto-generated** from missing meal ingredients
- **Priority-based** — items linked to today's meals rank higher
- **Budget-aware** — greedy selection within your weekly budget
- **Manual item management** — add items, toggle needed/bought
- **Export** as CSV or plain text

### 💰 Budget Tracking
- Set **weekly grocery budget** with currency
- Real-time cost estimation using category-based pricing
- Budget remaining calculated against shopping list totals

### 📅 AI Weekly Planner
- **One-click plan generation** powered by [LangGraph](https://github.com/langchain-ai/langgraph)
- Orchestrates: urgency analysis → meal generation → shopping list → AI summary
- **Plan persistence** — saves snapshots for later review
- **Natural-language explanation** of your weekly plan

### 📊 Dashboard
- At-a-glance stats: pantry count, expiring soon, expired items
- Top urgent items with urgency scores
- Quick meal suggestions for today
- Shopping list count and budget status

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript 6, Vite 8, React Router 7 |
| **Backend** | Django 6.0, Django REST Framework 3.17 |
| **Database** | PostgreSQL (NeonDB) with SQLite fallback |
| **AI** | Google Gemini 2.5 Flash (via REST API) |
| **Orchestration** | LangGraph (state-graph pipeline) |
| **Auth** | JWT via SimpleJWT (access + refresh tokens) |

---

## 📁 Project Structure

```
PantryFlow/
├── .env                          # Environment variables (not committed)
├── .gitignore
├── README.md
├── backend/
│   ├── manage.py                 # Django CLI entry point
│   ├── requirements.txt          # Python dependencies
│   ├── pantryflow/               # Django project config
│   │   ├── settings.py           # Settings (DB, JWT, CORS, apps)
│   │   ├── urls.py               # Root URL routing
│   │   ├── wsgi.py / asgi.py
│   ├── accounts/                 # Auth & user management
│   │   ├── models.py             # CustomUser (email-based)
│   │   ├── views.py              # Register, Login, Logout, Me
│   │   ├── serializers.py        # Auth serializers
│   │   └── urls.py
│   ├── core/                     # Health check & dashboard
│   │   ├── views.py              # /health/, /dashboard/
│   │   └── urls.py
│   ├── pantry/                   # Inventory CRUD
│   │   ├── models.py             # PantryItem model
│   │   ├── views.py              # ViewSet with filtering
│   │   ├── serializers.py        # Validation logic
│   │   ├── admin.py              # Django admin config
│   │   └── management/commands/  # seed_pantry command
│   ├── meals/                    # Meal suggestion engine
│   │   ├── models.py             # GeneratedMealSet, GeneratedMeal
│   │   ├── views.py              # Scoring, grouping, matching
│   │   ├── generator.py          # LLM prompt & response parsing
│   │   ├── cache.py              # SHA-256 pantry hash caching
│   │   └── tests.py
│   ├── ai_service/               # Gemini AI abstraction
│   │   ├── provider.py           # GeminiProvider class
│   │   ├── views.py              # AI explanation endpoints
│   │   ├── serializers.py        # Request validation
│   │   └── tests.py
│   ├── planning/                 # Budget & shopping list
│   │   ├── models.py             # WeeklyBudget, ShoppingListItem
│   │   ├── views.py              # Budget CRUD, shopping generation
│   │   ├── serializers.py        # Budget & shopping serializers
│   │   └── tests.py
│   └── planner/                  # LangGraph weekly planner
│       ├── graph.py              # State graph definition
│       ├── models.py             # AIPlanSession
│       ├── views.py              # Plan endpoints
│       └── tests.py
└── frontend/
    ├── index.html
    ├── package.json              # Node dependencies
    ├── vite.config.ts            # Dev proxy to Django
    ├── tsconfig.json
    └── src/
        ├── main.tsx              # React entry (BrowserRouter + AuthProvider)
        ├── App.tsx               # Route definitions
        ├── App.css               # Application styles
        ├── index.css             # Global styles & CSS variables
        ├── api/                  # API client modules
        │   ├── authApi.ts        # JWT token management
        │   ├── pantryApi.ts      # Pantry CRUD
        │   ├── mealsApi.ts       # Meal suggestions
        │   ├── planningApi.ts    # Budget & shopping
        │   ├── aiApi.ts          # AI explanations
        │   ├── dashboardApi.ts   # Dashboard stats
        │   └── plannerApi.ts     # Weekly planner
        ├── context/
        │   └── AuthContext.tsx    # Auth state management
        ├── hooks/
        │   └── useToast.ts       # Toast notifications
        ├── components/
        │   ├── EmptyState.tsx     # Empty state placeholder
        │   └── Toast.tsx         # Toast notification UI
        ├── layout/
        │   └── RootLayout.tsx    # Header, nav, footer
        └── pages/
            ├── Home.tsx          # Dashboard
            ├── Pantry.tsx        # Inventory management
            ├── Meals.tsx         # Meal suggestions
            ├── ShoppingList.tsx  # Shopping list
            ├── Budget.tsx        # Budget management
            ├── Planner.tsx       # Weekly planner
            ├── Login.tsx         # Login form
            ├── Register.tsx      # Registration form
            └── NotFound.tsx      # 404 page
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.14+** with pip
- **Node.js 18+** with npm
- (Optional) **PostgreSQL** — falls back to SQLite if `DATABASE_URL` is not set

### 1. Clone the Repository

```bash
git clone https://github.com/Ajita369/PantryFlow.git
cd PantryFlow
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: PostgreSQL (NeonDB) connection
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require

# Optional: override the default Django secret key in production
DJANGO_SECRET_KEY=your_secret_key_here
```


### 3. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations
python backend/manage.py migrate

# (Optional) Seed sample pantry data
python backend/manage.py seed_pantry

# Start the development server
python backend/manage.py runserver
```

The API will be available at `http://localhost:8000`. Health check: `GET /api/health/`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`. The Vite dev proxy forwards all `/api/*` requests to the Django backend.

### 5. Create an Account

1. Navigate to `http://localhost:5173/register`
2. Sign up with email and password
3. You'll be automatically logged in and redirected to the dashboard

---

## 📡 API Reference

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register/` | — | Register with email + password |
| `POST` | `/api/auth/login/` | — | Login, returns JWT tokens + user |
| `POST` | `/api/auth/logout/` | JWT | Blacklist refresh token |
| `GET` | `/api/auth/me/` | JWT | Get current user profile |
| `PATCH` | `/api/auth/me/` | JWT | Update profile fields |
| `POST` | `/api/auth/refresh/` | — | Refresh access token |

### Pantry
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/pantry-items/` | JWT | List items (supports `?search=` and `?category=`) |
| `POST` | `/api/pantry-items/` | JWT | Create item |
| `GET` | `/api/pantry-items/{id}/` | JWT | Get item |
| `PUT` | `/api/pantry-items/{id}/` | JWT | Update item |
| `DELETE` | `/api/pantry-items/{id}/` | JWT | Delete item |
| `GET` | `/api/pantry-items/expired/` | JWT | Items past expiry |
| `GET` | `/api/pantry-items/expiring-soon/` | JWT | Items expiring within `?days=7` |

### Meals
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/meals/suggestions/` | JWT | Get meal suggestions (cached) |
| `POST` | `/api/meals/generate/` | JWT | Force regenerate meals |

### Budget & Shopping List
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/budget/` | JWT | Get current weekly budget |
| `POST` | `/api/budget/` | JWT | Create/update budget |
| `GET` | `/api/shopping-list/` | JWT | List shopping items with totals |
| `PATCH` | `/api/shopping-list/{id}/` | JWT | Update item (toggle needed, priority) |
| `POST` | `/api/shopping-list/generate/` | JWT | Auto-generate from meals |
| `POST` | `/api/shopping-list/add-items/` | JWT | Add items manually |
| `GET` | `/api/shopping-list/export/` | JWT | Export as CSV or text (`?format=csv\|text`) |

### AI Service
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/ai/meal-explanation/` | JWT | AI explanation for a meal |
| `POST` | `/api/ai/substitution/` | JWT | Substitution suggestions |
| `POST` | `/api/ai/shopping-notes/` | JWT | Budget-aware shopping advice |

### Weekly Planner
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/plan-week/` | JWT | Get last saved plan |
| `POST` | `/api/plan-week/` | JWT | Generate new weekly plan |

### System
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health/` | — | Health check |
| `GET` | `/api/dashboard/` | JWT | Aggregated dashboard data |

---

## 🧪 Running Tests

```bash
# Run all backend tests
python backend/manage.py test

# Run tests for a specific app
python backend/manage.py test meals
python backend/manage.py test planning
python backend/manage.py test ai_service
python backend/manage.py test planner
```


## 🔄 How It Works

### Meal Suggestion Pipeline

1. **Pantry Hashing** — SHA-256 hash of all pantry items determines if meals need regeneration
2. **AI Generation** — Sends pantry items to Gemini 2.5 Flash with a structured prompt; falls back to 5 built-in templates on failure
3. **Ingredient Matching** — Each meal's ingredients are matched against pantry contents
4. **Urgency Scoring** — Items nearing expiry get higher priority (0-100 score)
5. **Match Scoring** — `matched / total` ratio with a +0.1 bonus for urgent ingredients
6. **Group Assignment** — Meals sorted into Cook Today (≥75% match), Cook This Week (≥50%), Possible Later
7. **Rebalancing** — Ensures minimum counts per group
8. **Persistence** — Results cached in DB, invalidated on pantry changes

### Weekly Planning (LangGraph)

A 6-node state graph pipeline:
1. **Load Data** → Fetch pantry + budget
2. **Compute Urgency** → Score every item
3. **Decide Tasks** → Plan scope + warnings
4. **Build Meals** → Generate/cache meals + substitutions
5. **Build Shopping** → Budget-constrained list from meal gaps
6. **Build Explanation** → AI-generated plan summary


