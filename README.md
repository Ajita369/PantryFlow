# PantryFlow

Phase 1 delivers a full-stack skeleton with a Vite + React frontend and a Django + DRF backend.

## Prerequisites
- Node.js 18+
- Python 3.14+

## Backend setup
1. Create or activate the virtual environment.
2. Install dependencies:
   ```bash
   .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
   ```
3. Run migrations:
   ```bash
   .venv\Scripts\python.exe backend\manage.py migrate
   ```
4. Start the server:
   ```bash
   .venv\Scripts\python.exe backend\manage.py runserver
   ```

The health check is available at `/api/health/`.

## Frontend setup
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the dev server:
   ```bash
   npm run dev
   ```

The frontend uses a dev proxy so `/api/*` routes hit the Django server at `http://localhost:8000`.

## Next phases
Continue with Phase 2 for Pantry CRUD and validation.
