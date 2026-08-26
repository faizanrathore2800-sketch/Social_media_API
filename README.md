# Social Media API

A REST API for a small social platform — users can register, log in, create posts, and upvote each other's posts. Built with FastAPI, PostgreSQL, and JWT authentication.

## Project Evolution

This project started in 2025 as a from-scratch FastAPI backend covering the core fundamentals: relational data modeling, SQLAlchemy ORM relationships, Alembic migrations, password hashing, and JWT-based authentication.

Revisiting it since, I added:

- **A frontend, "Echo"** — the project was API-only before; `frontend/` now provides a working UI to register, log in, browse/search posts, create and edit posts, and vote, entirely through the existing API.
- **A real security fix** — the original `.env` file (containing the database password and JWT signing key) had been committed to version control. It's now removed from tracking, `.gitignore` is fixed (the original had a file-encoding bug that likely caused it to silently not work), and a `.env.example` documents the required variables without exposing real values.
- **A CORS fix** — the original CORS configuration allowed `https://www.google.com`, which didn't match any real client. It now correctly allows the local frontend's origin.

The original backend commits are left untouched below this point in the repo's history — this README's job is to make the "before vs. after" legible at a glance rather than rewriting the story.

## Features

- User registration and JWT-based login
- Create, read, update, and delete posts (owner-only for edit/delete)
- Upvote / remove-vote on posts, with vote counts
- Search and paginate posts
- Alembic migrations tracking schema changes over time
- Echo — a Streamlit-based frontend for all of the above

## Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic, python-jose (JWT), passlib/bcrypt
**Frontend:** Streamlit, Requests

## Project Structure

```
Social_media_API/
├── app/
│   ├── main.py          # FastAPI app, CORS, routers
│   ├── config.py        # Environment-driven settings
│   ├── database.py      # SQLAlchemy engine/session
│   ├── models.py        # User, Post, Vote
│   ├── schemas.py       # Pydantic request/response models
│   ├── oauth2.py         # JWT creation/verification
│   ├── utils.py          # Password hashing
│   └── routers/          # users, auth, post, vote
├── alembic/               # Database migrations
├── frontend/               # "Echo" - the UI
│   ├── app.py             # Streamlit UI
│   ├── api_client.py      # Backend HTTP client
│   ├── .streamlit/config.toml
│   └── requirements.txt
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

Requires Python 3.11+ and a local PostgreSQL instance.

### 1. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your local Postgres credentials and a freshly generated secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Create the database

```sql
CREATE DATABASE social_media_api;
```

(Or reuse an existing database — just make sure `DATABASE_NAME` in `.env` matches.)

### 3. Backend

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

### 4. Frontend

In a second terminal, with the backend already running:

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Visit `http://localhost:8501`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/users/` | Register a new user |
| GET | `/users/{id}` | Get a user by ID |
| POST | `/login` | Log in, returns a JWT access token |
| GET | `/posts/` | List posts (filter with `search`, paginate with `limit`/`skip`) |
| POST | `/posts/` | Create a post |
| GET | `/posts/{id}` | Get a single post with its vote count |
| PUT | `/posts/{id}` | Update a post (owner only) |
| DELETE | `/posts/{id}` | Delete a post (owner only) |
| POST | `/vote/` | Vote on a post (`dir: 1` to add, `dir: 0` to remove) |

Full interactive documentation is available at `/docs` once the backend is running.

## Security Note

If you're looking at the git history: an earlier commit contains a `.env` file with a database password and JWT secret. The JWT secret has been rotated and is no longer valid. **The database password should also be changed** (`ALTER USER ... WITH PASSWORD ...` in psql) since it was exposed the same way — that's a local credential change only the repo owner can make, so it isn't done as part of this commit. Either way, `.env` is now excluded from version control going forward via a corrected `.gitignore` (the original had a file-encoding bug that likely caused it to silently never take effect). This is left visible in history deliberately, alongside the fix, rather than rewritten away.

## License

MIT
