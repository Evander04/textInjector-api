# Recruiter API — Flask Boilerplate (Dev/Prod Ready)

A clean, secure, and scalable Flask WebAPI for a recruiter platform with:
- Proper **dev/prod config separation**
- **PostgreSQL** via SQLAlchemy + Flask-Migrate
- **Environment variables** via `.env` (kept out of Git)
- **Modular controllers** (users, clients) and models
- Ready to run locally or in containers later

---

## 📁 Project Structure
```
recruiter_api/
│── run.py
│── requirements.txt
│── .env                # your local secrets (NOT committed)
│── .env.example        # template for teammates/CI
│── .gitignore
│
├── app/
│   ├── __init__.py            # app factory; loads config by APP_ENV
│   ├── extensions.py          # db, migrate
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py            # common settings
│   │   ├── dev.py             # DevConfig
│   │   └── prod.py            # ProdConfig
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── client.py
│   │
│   └── controllers/
│       ├── __init__.py
│       ├── health.py          # /api/health
│       ├── users.py           # /api/users
│       └── clients.py         # /api/clients
│
└── migrations/                # created by Flask-Migrate (after init)
```

---

## 🧰 Requirements
- Python 3.8+
- PostgreSQL 12+ running locally (or a remote instance)
- `psql` CLI (optional but handy)
- Recommended: a Python virtual environment

---

## ⚙️ 1) Setup Environment

1) **Create virtual environment & install deps**
```bash
python3 -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2) **Create your `.env`** (copy the template and edit values)
```bash
cp .env.example .env
```

Edit `.env` (examples below). We use **APP_ENV** for config selection (instead of deprecated `FLASK_ENV`):
```ini
APP_ENV=development
FLASK_DEBUG=1
SECRET_KEY=super-secret-key

DEV_DATABASE_URL=postgresql://devuser:devpass@localhost:5432/recruiter_dev
PROD_DATABASE_URL=postgresql://produser:prodpass@localhost:5432/recruiter_prod
```

> **Note:** `FLASK_ENV` is deprecated in Flask 2.3+. We use `APP_ENV` (`development` or `production`) to select config, and `FLASK_DEBUG` to toggle debug mode.

---

## 🗃️ 2) Create PostgreSQL User & Databases

**Option A: Use your own existing Postgres user** and just create DBs:
```bash
psql -U postgres -c "CREATE DATABASE paperwork_dev;"
psql -U postgres -c "CREATE DATABASE paperwork_prod;"
```

**Option B: Create a dedicated user (recommended):**
```sql
-- In psql:
CREATE USER devuser WITH PASSWORD 'devpass';
CREATE DATABASE recruiter_dev OWNER devuser;
GRANT ALL PRIVILEGES ON DATABASE recruiter_dev TO devuser;

CREATE USER produser WITH PASSWORD 'prodpass';
CREATE DATABASE recruiter_prod OWNER produser;
GRANT ALL PRIVILEGES ON DATABASE recruiter_prod TO produser;
```

Update `.env` to match your credentials.

---

## 🧱 3) Initialize & Apply Migrations
```bash
# Make sure venv is active and .env is configured
flask db init                      # first time only; creates migrations/ folder
flask db migrate -m "Initial"
flask db upgrade
```

---

## ▶️ 4) Run the API
```bash
# Development
APP_ENV=development FLASK_DEBUG=1 python run.py

# Production-like local run (still uses run.py; for true prod use WSGI server)
APP_ENV=production FLASK_DEBUG=0 python run.py
```

API base URL: `http://127.0.0.1:5000/api`

- Health: `GET /api/health`
- Users:  `GET /api/users/`, `POST /api/users/`
- Clients: `GET /api/clients/`, `POST /api/clients/`

---

## 🧪 5) Quick Test (curl)

**Health**
```bash
curl http://127.0.0.1:5000/api/health
```

**Create user**
```bash
curl -X POST http://127.0.0.1:5000/api/users/   -H "Content-Type: application/json"   -d '{"name":"Jane Doe","email":"jane@example.com"}'
```

**List users**
```bash
curl http://127.0.0.1:5000/api/users/
```

---

## 🔐 Security & Git Hygiene
- Secrets live in `.env` (already in `.gitignore`).
- Share `.env.example` with teammates; never commit real secrets.
- Use least-privilege DB users and rotate credentials in prod.

---

## 🛠️ Troubleshooting

**`ModuleNotFoundError: No module named 'app'`**
- Ensure you run from project root: `python run.py`
- `run.py` already adds project root to `PYTHONPATH`.

**`FLASK_ENV is deprecated` warning**
- This boilerplate uses `APP_ENV` and `FLASK_DEBUG` instead.

**DB connect errors**
- Verify your `DEV_DATABASE_URL`/`PROD_DATABASE_URL` credentials and DB name.
- Ensure Postgres is running and accepting connections on the configured host/port.

---

## 📦 Next Steps
- Add more controllers under `app/controllers/*.py`
- Add services under `app/services/*` if business logic grows
- Consider adding Docker & docker-compose for infra parity
