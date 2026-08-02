data "aws_iam_policy_document" "github_deploy" {
  statement {
    sid    = "LambdaCodeDeploy"
    effect = "Allow"
    actions = [
      "lambda:UpdateFunctionCode",
      "lambda:GetFunction",
      "lambda:GetFunctionConfiguration",
    ]
    resources = [aws_lambda_function.api.arn]
  }
}

# Attached to the consolidated role (data.aws_ssm_parameter.deploy_role_name
# in main.tf).
resource "aws_iam_role_policy" "gha_deploy" {
  name   = "gha-deploy-resume-api"
  role   = data.aws_ssm_parameter.deploy_role_name.value
  policy = data.aws_iam_policy_document.github_deploy.json
}
