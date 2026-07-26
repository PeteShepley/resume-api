# Custom domain: resume.api.peteshepley.com. Wildcard cert for
# *.api.peteshepley.com is managed in infra/003-dns (shared across every
# API that adopts this convention, not resume-api-specific) — looked up
# here by domain name rather than passed in as a variable/remote state
# output, same cross-stack pattern used for the *.peteshepley.com cert in
# infra/002-static-site.
data "aws_acm_certificate" "api_wildcard" {
  domain      = "api.peteshepley.com"
  statuses    = ["ISSUED"]
  types       = ["AMAZON_ISSUED"]
  most_recent = true
}

resource "aws_apigatewayv2_domain_name" "resume_api" {
  domain_name = "resume.api.peteshepley.com"

  domain_name_configuration {
    certificate_arn = data.aws_acm_certificate.api_wildcard.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "resume_api" {
  api_id      = aws_apigatewayv2_api.resume_api.id
  domain_name = aws_apigatewayv2_domain_name.resume_api.id
  stage       = aws_apigatewayv2_stage.default.id
}
