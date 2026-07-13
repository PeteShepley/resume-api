"""Lambda entrypoint -- mounts every router under /me and resolves requests.

Every request's identity is verified in-app (see auth.py/clerk.py) from
the Authorization header directly; nothing here trusts an upstream proxy
or authorizer to have already done it, so behavior is identical whether
this runs behind API Gateway or standalone via local_server.py.
"""

import os

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.api_gateway import CORSConfig

from resume_api.routers import certifications, education, experience, goals, hobbies, profile, resume, skills

# CORS is only ever enabled for local dev (see local_server.py, which sets
# LOCAL_DEV) -- production's response headers are unaffected.
_cors = (
    CORSConfig(allow_origin=os.environ.get("CORS_ALLOW_ORIGIN", "*"))
    if os.environ.get("LOCAL_DEV")
    else None
)

app = APIGatewayHttpResolver(cors=_cors)

app.include_router(profile.router, prefix="/me/profile")
app.include_router(experience.router, prefix="/me/experience")
app.include_router(education.router, prefix="/me/education")
app.include_router(skills.router, prefix="/me/skills")
app.include_router(certifications.router, prefix="/me/certifications")
app.include_router(hobbies.router, prefix="/me/hobbies")
app.include_router(goals.router, prefix="/me/goals")
app.include_router(resume.router, prefix="/me/resume")


def handler(event, context):
    return app.resolve(event, context)
