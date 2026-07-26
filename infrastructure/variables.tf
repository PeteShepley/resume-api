variable "aws_region" {
  description = "AWS region for resume-api resources"
  type        = string
  default     = "us-east-1"
}

# Empty until the Clerk application exists — see
# docs/runbooks/resume-api-deployment.md. AWS validates a JWT authorizer's
# issuer by actually reaching its /.well-known/openid-configuration at
# creation time, so a fake placeholder URL fails outright (there's no way to
# create it "unvalidated" and fix it later). Left empty, the authorizer and
# the API's only route are simply not created (see apigateway.tf) — the API
# fails closed (every request 404s) rather than ever being open without
# auth. Set both to real values and re-apply once the Clerk app exists.
variable "clerk_issuer_url" {
  description = "Clerk instance issuer URL (Frontend API URL) used by the API Gateway JWT authorizer"
  type        = string
  default     = "https://fine-elf-56.clerk.accounts.dev"
}

variable "clerk_audience" {
  description = "Audience of the Clerk JWT template used to sign tokens for this API"
  type        = string
  default     = "https://resume.api.peteshepley.com"
}

variable "github_owner" {
  description = "GitHub organization or user that owns the repositories managed in this stack"
  type        = string
  default     = "PeteShepley"
}

variable "github_repo" {
  description = "GitHub repository allowed to assume the deploy role (format: owner/repo)"
  type        = string
  default     = "PeteShepley/resume-api"
}

variable "cors_allowed_origins" {
  description = "Browser origins allowed to call this API cross-origin (API Gateway's native CORS support)"
  type        = list(string)
  default     = ["https://test.peteshepley.com", "https://resume.peteshepley.com", "http://localhost:5173"]
}
