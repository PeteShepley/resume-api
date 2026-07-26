# Terraform owns this function's shell; the resume-api repo's deploy.yml owns
# its code via `aws lambda update-function-code`. The placeholder zip below
# only exists so this stack can be applied before that repo has any code —
# ignore_changes keeps a later `tofu apply` from reverting a real deploy,
# the same split already used for the static site (Terraform owns the S3
# bucket; CI owns its contents).

data "archive_file" "placeholder" {
  type        = "zip"
  source_dir  = "${path.module}/lambda-placeholder"
  output_path = "${path.module}/.placeholder.zip"
}

resource "aws_iam_role" "lambda_exec" {
  name = "resume-api-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_dynamodb" {
  statement {
    sid    = "ResumeTableAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
    ]
    resources = [aws_dynamodb_table.resume.arn]
  }
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name   = "resume-api-dynamodb"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_dynamodb.json
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/resume-api"
  retention_in_days = 14
}

resource "aws_lambda_function" "api" {
  function_name = "resume-api"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "resume_api.app.handler"
  runtime       = "python3.13"
  timeout       = 10
  memory_size   = 256

  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.resume.name
      CLERK_ISSUER_URL = "https://fine-elf-56.clerk.accounts.dev"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb,
    aws_cloudwatch_log_group.api,
  ]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}
