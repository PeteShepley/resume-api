# resume-api

An API for a person's resume-shaped data — profile, work experience,
education, skills, certifications, hobbies, and goals — served back as JSON
or Markdown. Individuals authenticate via [Clerk](https://clerk.com) and can
only ever access their own data. Python on AWS Lambda, DynamoDB, and API
Gateway.

Every request's identity is verified by the app itself (see `auth.py` /
`clerk.py`): the bearer token on the `Authorization` header is checked
against Clerk's published JWKS directly, so behavior is identical whether
this runs behind API Gateway in AWS or standalone on your own machine.

Data model: everything lives in one DynamoDB table, keyed by
`pk=USER#<clerk_user_id>` and an `sk` that says what the item is —
`PROFILE` for the profile singleton, `<ENTITY_TYPE>#<uuid>` (e.g.
`EXPERIENCE#<uuid>`) for each item in the six owned collections. See
`db.py` for the key-building helpers and `models.py` for the entity types.

## Structure

```
src/resume_api/
  app.py            Lambda entrypoint — mounts every router, resolves requests
  local_server.py   local dev HTTP server — translates real HTTP <-> the same event shape app.py resolves
  clerk.py          fetches/caches Clerk's JWKS, verifies a bearer token's signature/issuer/audience/expiry
  auth.py           extracts the caller's Clerk user id from a verified token (via clerk.py)
  db.py             DynamoDB table handle, pk/sk helpers, Decimal <-> number conversion
  crud.py           generic list/create/get/update/delete router factory
  models.py         Pydantic models for every entity
  markdown.py       resume dict -> Markdown renderer
  routers/
    profile.py      singleton GET/PUT (hand-written — doesn't fit the CRUD factory)
    experience.py    = crud.build_collection_router(...), same for the other five
    education.py       collections (skills, certifications, hobbies, goals)
    resume.py        aggregate GET, JSON or Markdown
tests/              pytest, one module per router group, plus test_auth.py for token verification
```

## Commands

| Command                                             | Action                             |
|:----------------------------------------------------|:-----------------------------------|
| `python -m venv .venv && source .venv/bin/activate` | Create/activate a virtualenv       |
| `pip install -r requirements-dev.txt`               | Install runtime + dev dependencies |
| `pytest`                                            | Run the test suite                 |
| `ruff check .`                                      | Lint                               |
| `./scripts/run-local.sh`                            | Run the API locally (see below)    |

## Running locally

Lets another application (a frontend, a script, Postman) develop against
this API with no AWS account and no deployment — just this repo, Docker,
and a Clerk application to issue tokens against.

Prerequisites:
- Docker (for DynamoDB Local)
- A Clerk instance to authenticate against — reuse the same one your
  frontend/dev environment already uses, or a throwaway Clerk dev instance

```
pip install -r requirements-dev.txt
CLERK_ISSUER_URL=https://your-app.clerk.accounts.dev ./scripts/run-local.sh
```

This starts DynamoDB Local (`docker compose up -d dynamodb-local`,
in-memory — data resets whenever the container restarts), creates the
table if it doesn't exist yet, and serves the API on
`http://localhost:8000` with CORS enabled for browser callers. Call it the
same way you'd call the deployed API:

```
curl http://localhost:8000/me/profile \
  -H "Authorization: Bearer <a real Clerk session token>"
```

Set `CLERK_AUDIENCE` too if your Clerk JWT template enforces one. `PORT`
and `TABLE_NAME` are also overridable; see `scripts/run-local.sh` for every
env var it reads and its default.

## Endpoints

All routes are scoped to the caller's own Clerk user id (`/me/...` — no
person id ever appears in a URL). See `openapi/resume-api.yaml` for the
full endpoint/schema reference; summary:

- `GET`/`PUT /me/profile`
- `GET`/`POST /me/{experience,education,skills,certifications,hobbies,goals}`
- `GET`/`PUT`/`DELETE /me/{collection}/{id}`
- `GET /me/resume?format=json|markdown` — the whole resume assembled in one call

## Deployment

Deploys via GitHub Actions on every push to `main` (`.github/workflows/deploy.yml`):
build a zip with `requirements.txt` installed alongside `src/resume_api/`,
then `aws lambda update-function-code`. Authentication is via GitHub OIDC (no
stored AWS credentials) — the function, table, and API Gateway are
provisioned in `operations/infra/apis/resume-api`. Pull requests run
`.github/workflows/ci.yml` (`ruff check` + `pytest`) without touching any
deployment credentials.

Required repo configuration (see
`operations/docs/runbooks/resume-api-deployment.md` for how to get these
values, and for the Clerk application setup this API depends on):

| Name                   | Kind             | Value                                                                      |
|:-----------------------|:-----------------|:---------------------------------------------------------------------------|
| `AWS_ROLE_ARN`         | Actions secret   | `tofu output github_deploy_role_arn` in `operations/infra/apis/resume-api` |
| `LAMBDA_FUNCTION_NAME` | Actions variable | `tofu output lambda_function_name` in `operations/infra/apis/resume-api`   |

The app verifies every caller's token itself (see "Structure" above) using
the `CLERK_ISSUER_URL`/`CLERK_AUDIENCE` Lambda environment variables. Until
those are set, every request 401s — it fails closed rather than ever being
reachable without a verified identity.
