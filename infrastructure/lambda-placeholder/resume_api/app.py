"""Placeholder Lambda handler.

Terraform creates the function with this code so the stack can be applied
before the resume-api repo exists. The repo's deploy.yml replaces it via
`aws lambda update-function-code` on the first push to main — see
docs/runbooks/resume-api-deployment.md.
"""


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "resume-api placeholder — deploy.yml has not shipped real code yet"}',
    }
