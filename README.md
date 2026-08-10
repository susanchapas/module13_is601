# Calculations API

FastAPI application with JWT authentication and a calculation store. Users register and log in from server-rendered pages; the browser keeps the access token in `localStorage` and sends it as a bearer token on every calculation request. Data lives in PostgreSQL through SQLAlchemy.

## Routes

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/` | — | Home page |
| GET | `/login` | — | Login page |
| GET | `/register` | — | Registration page |
| GET | `/dashboard` | — | Dashboard page |
| GET | `/health` | — | Health check, used by Docker and CI |
| POST | `/auth/register` | — | Create a user. 400 if the username or email exists |
| POST | `/auth/login` | — | JSON login. Returns access and refresh tokens |
| POST | `/auth/token` | — | Form login for the Swagger UI |
| POST | `/calculations` | Bearer | Compute and store a calculation |
| GET | `/calculations` | Bearer | List the current user's calculations |
| GET | `/calculations/{id}` | Bearer | Read one calculation |
| PUT | `/calculations/{id}` | Bearer | Update the inputs and recompute |
| DELETE | `/calculations/{id}` | Bearer | Delete a calculation |

Calculation types: `addition`, `subtraction`, `multiplication`, `division`.

Interactive docs: `/docs`.

## Run with Docker Compose

```bash
cp .env.example .env
# JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY are required and have no defaults
openssl rand -hex 32   # paste into each key in .env

docker compose up --build
```

The app is on http://localhost:8000 and PostgreSQL on port 5432. `docker-compose.override.yml` is applied automatically for development: it bind-mounts the repository and runs uvicorn with `--reload`. For a production-like run that uses only the image contents:

```bash
docker compose -f docker-compose.yml up --build
```

## Run locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt   # requirements.txt is runtime only
playwright install --with-deps chromium

docker compose up -d db          # or point DATABASE_URL at your own PostgreSQL
python -m app.database_init      # creates the tables
uvicorn app.main:app --reload
```

Styles are Tailwind, compiled ahead of time into `static/css/tailwind.css`. After changing a template or `static/css/input.css`:

```bash
npm install
npm run build:css
```

## Tests

`pytest.ini` already enables coverage over `app/`. The e2e tier starts its own uvicorn subprocess and drives Chromium with Playwright, so the database must be reachable.

```bash
pytest                     # all tiers
pytest tests/unit          # pure operation logic
pytest tests/integration   # models, schemas, and auth against a real database
pytest tests/e2e           # browser tests, positive and negative
```

Useful options: `--preserve-db` keeps the tables after the run, `--run-slow` includes tests marked slow.

When an e2e test fails, a full-page screenshot and a Playwright trace are written to `test-results/`. Open a trace with:

```bash
playwright show-trace test-results/<test_name>.trace.zip
```

Coverage HTML lands in `htmlcov/`.

## CI/CD

`.github/workflows/test.yml` runs on every push and pull request to `main`:

```
test → build → scan → push → smoke
```

- **test** — installs dependencies, runs every tier against a PostgreSQL service, uploads `test-results/` and `htmlcov/` even on failure.
- **build** — builds the image once and saves it as a workflow artifact.
- **scan** — loads that exact image and fails on CRITICAL or HIGH vulnerabilities that have a fix. Accepted findings go in `.trivyignore` with a date and a reason.
- **push** — `main` only. Pushes the scanned image, so the scanned bytes are the published bytes, tagged `latest` and the commit SHA.
- **smoke** — runs the published image against PostgreSQL, waits for `/health`, then registers and logs in over HTTP.

### Required GitHub secrets

| Secret | Purpose |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub account. Also the image namespace: `<username>/module13_is601` |
| `DOCKERHUB_TOKEN` | Docker Hub access token with write scope |

The `push` job targets the `production` environment, so add both secrets there if that environment restricts them.

## Configuration

All settings come from the environment or `.env` (see `.env.example`).

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | local PostgreSQL | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | — | Required. Signs access tokens |
| `JWT_REFRESH_SECRET_KEY` | — | Required. Signs refresh tokens |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `BCRYPT_ROUNDS` | `12` | Password hashing cost |

Never commit a real `.env`; it is git-ignored.
