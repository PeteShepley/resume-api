#!/usr/bin/env bash
# Runs the API locally against DynamoDB Local, for another app to develop
# against without any AWS infrastructure. See README.md "Running locally".
set -euo pipefail

: "${CLERK_ISSUER_URL:?Set CLERK_ISSUER_URL to your Clerk instance, e.g. https://your-app.clerk.accounts.dev}"
export CLERK_ISSUER_URL
export CLERK_AUDIENCE="${CLERK_AUDIENCE:-}"

export TABLE_NAME="${TABLE_NAME:-resume-api-local}"
export AWS_ENDPOINT_URL_DYNAMODB="${AWS_ENDPOINT_URL_DYNAMODB:-http://localhost:8001}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-local}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-local}"

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Not pip-installed (see pyproject.toml) -- put src/ on the path the same
# way pytest's `pythonpath = ["src"]` setting does.
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"

docker compose up -d dynamodb-local
exec python -m resume_api.local_server
