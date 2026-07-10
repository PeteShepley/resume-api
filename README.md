# resume-api

An API for a person's resume-shaped data — profile, work experience,
education, skills, certifications, hobbies, and goals — served back as JSON
or Markdown. Individuals authenticate via [Clerk](https://clerk.com) and can
only ever access their own data. Python on AWS Lambda, DynamoDB, and API
Gateway.

For why things are built this way, and how the deployment infra fits
together, see the design doc and build journal in the sibling `operations`
repo: `operations/docs/projects/resume-api/design.md` and
`operations/docs/projects/resume-api/journal.md`.

## Structure

```
src/resume_api/
  app.py            Lambda entrypoint — mounts every router, resolves requests
  auth.py           extract the caller's Clerk user id from verified JWT claims
  db.py             DynamoDB table handle, pk/sk helpers, Decimal <-> number conversion
  crud.py           generic list/create/get/update/delete router factory
  models.py         Pydantic models for every entity
  markdown.py       resume dict -> Markdown renderer
  routers/
    profile.py      singleton GET/PUT (hand-written — doesn't fit the CRUD factory)
    experience.py    = crud.build_collection_router(...), same for the other five
    education.py       collections (skills, certifications, hobbies, goals)
    resume.py        aggregate GET, JSON or Markdown
tests/              pytest + moto (mocked DynamoDB), one module per router group
```

## Commands

| Command | Action |
|:---|:---|
| `python -m venv .venv && source .venv/bin/activate` | Create/activate a virtualenv |
| `pip install -r requirements-dev.txt` | Install runtime + dev dependencies |
| `pytest` | Run the test suite |
| `ruff check .` | Lint |

## Endpoints

All routes are scoped to the caller's own Clerk user id (`/me/...` — no
person id ever appears in a URL). See the design doc for the full endpoint
table; summary:

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

| Name | Kind | Value |
|:---|:---|:---|
| `AWS_ROLE_ARN` | Actions secret | `tofu output github_deploy_role_arn` in `operations/infra/apis/resume-api` |
| `LAMBDA_FUNCTION_NAME` | Actions variable | `tofu output lambda_function_name` in `operations/infra/apis/resume-api` |

Until a Clerk application exists and `clerk_issuer_url`/`clerk_audience` are
set in that Terraform stack, the API has no route at all (every request
404s) — it fails closed rather than ever being reachable without auth.
