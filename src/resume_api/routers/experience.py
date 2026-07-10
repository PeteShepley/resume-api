"""Experience collection routes — CRUD logic lives in resume_api.crud."""

from resume_api.crud import build_collection_router
from resume_api.models import Experience

router = build_collection_router("EXPERIENCE", Experience, sort_by="start_date", reverse=True)
