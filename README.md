# Task Manager (3-tier Python app)

- Frontend: Flask + HTML (port 8000)
- Backend: Flask REST API (port 5000)
- Database: PostgreSQL in Docker (port 5432)

## 1. Database (Docker)
    docker compose up -d

The table is created automatically from database/init.sql on first start.
Stop: `docker compose down` (data kept). Reset everything: `docker compose down -v`.

## 2. Backend
    cd backend
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python app.py

## 3. Frontend (new terminal)
    cd frontend
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python app.py

Open http://localhost:8000
