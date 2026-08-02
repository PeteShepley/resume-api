terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    bucket         = "peteshepley-ops-tofu-state"
    key            = "apis/resume-api/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "peteshepley-ops-tofu-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

# The consolidated per-repo GitHub OIDC deploy role (gha-deploy-resume-api),
# created in operations/infra/002-github-projects. iam.tf attaches a policy
# to it.
data "aws_ssm_parameter" "deploy_role_name" {
  name = "/github-deploy/resume-api/role-name"
}

data "aws_ssm_parameter" "deploy_role_arn" {
  name = "/github-deploy/resume-api/role-arn"
}
