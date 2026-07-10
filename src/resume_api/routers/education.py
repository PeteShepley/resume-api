"""Education collection routes — CRUD logic lives in resume_api.crud."""

from resume_api.crud import build_collection_router
from resume_api.models import Education

router = build_collection_router("EDUCATION", Education, sort_by="start_date", reverse=True)
