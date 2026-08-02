output "dynamodb_table_name" {
  description = "Name of the resume-api DynamoDB table"
  value       = aws_dynamodb_table.resume.name
}

output "dynamodb_table_arn" {
  description = "ARN of the resume-api DynamoDB table"
  value       = aws_dynamodb_table.resume.arn
}

output "lambda_function_name" {
  description = "Name of the resume-api Lambda function — set as LAMBDA_FUNCTION_NAME in the repo's Actions variables"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "ARN of the resume-api Lambda function"
  value       = aws_lambda_function.api.arn
}

output "api_endpoint" {
  description = "Base invoke URL for the HTTP API (execute-api.amazonaws.com — still live alongside the custom domain below)"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "custom_domain_url" {
  description = "Custom domain URL for the API"
  value       = "https://${aws_apigatewayv2_domain_name.resume_api.domain_name}"
}

output "custom_domain_target" {
  description = "Regional target domain name for the custom domain — set as resume_api_target_domain_name in infra/003-dns"
  value       = aws_apigatewayv2_domain_name.resume_api.domain_name_configuration[0].target_domain_name
}

output "custom_domain_hosted_zone_id" {
  description = "Hosted zone ID for custom_domain_target — set as resume_api_target_hosted_zone_id in infra/003-dns"
  value       = aws_apigatewayv2_domain_name.resume_api.domain_name_configuration[0].hosted_zone_id
}

output "github_deploy_role_arn" {
  description = "ARN for the GitHub Actions deploy role — set as AWS_ROLE_ARN in the repo's Actions secrets"
  sensitive   = true
  value       = data.aws_ssm_parameter.deploy_role_arn.value
}
