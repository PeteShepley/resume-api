"""Hobby collection routes — CRUD logic lives in resume_api.crud."""

from resume_api.crud import build_collection_router
from resume_api.models import Hobby

router = build_collection_router("HOBBY", Hobby)
