"""Lambda entrypoint — mounts every router under /me and resolves requests.

The gateway's JWT authorizer (see infra/apis/resume-api/apigateway.tf in the
operations repo) already verified the caller before this ever runs; internal
routing among the 30+ /me/... paths happens here, not at the gateway.
"""

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver

from resume_api.routers import certifications, education, experience, goals, hobbies, profile, resume, skills

app = APIGatewayHttpResolver()

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
