resource "aws_apigatewayv2_api" "resume_api" {
  name          = "resume-api"
  protocol_type = "HTTP"

  # Native HTTP API CORS support — API Gateway answers preflight OPTIONS
  # requests itself (never reaches the JWT authorizer or the Lambda), so
  # browser-based clients like api-console can call this cross-origin.
  cors_configuration {
    allow_origins = var.cors_allowed_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
    max_age       = 300
  }
}

# Not created until var.clerk_issuer_url is real — AWS validates the issuer's
# discovery endpoint at creation time, so a placeholder value can't be
# applied at all, let alone left in place safely. See variables.tf.
resource "aws_apigatewayv2_authorizer" "clerk" {
  count = var.clerk_issuer_url != "" ? 1 : 0

  api_id           = aws_apigatewayv2_api.resume_api.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "clerk"

  jwt_configuration {
    audience = [var.clerk_audience]
    issuer   = var.clerk_issuer_url
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.resume_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

# One route per verb this API actually uses (GET/POST/PUT/DELETE — see
# docs/projects/resume-api/design.md's endpoint table), all targeting the
# same catch-all integration; internal routing among the 30+ /me/... paths
# is handled by the Lambda's own router (Powertools
# APIGatewayHttpResolver), not by API Gateway. The authorizer runs once
# here, before the Lambda ever sees the request. Tied to the same count as
# the authorizer: no Clerk issuer means no routes, not unauthenticated ones.
#
# Deliberately NOT "ANY /{proxy+}": ANY matches OPTIONS too, which would
# route preflight requests through this JWT authorizer and 401 them —
# breaking every browser cross-origin call despite CORS being configured
# above. Explicit per-verb routes leave OPTIONS unmatched by any route, so
# API Gateway's native CORS support answers preflight itself (204, no
# Lambda invocation, no auth) instead. See docs/projects/api-console/journal.md.
resource "aws_apigatewayv2_route" "proxy" {
  for_each = var.clerk_issuer_url != "" ? toset(["GET", "POST", "PUT", "DELETE"]) : []

  api_id             = aws_apigatewayv2_api.resume_api.id
  route_key          = "${each.value} /{proxy+}"
  target             = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.clerk[0].id
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.resume_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.resume_api.execution_arn}/*/*"
}
