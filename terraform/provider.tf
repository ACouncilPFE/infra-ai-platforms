terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # For a portfolio project, local state is fine. In a real environment this
  # would be an S3 backend with DynamoDB state locking — see docs/adr/0002.
  #
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "infra-ai-platform/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "infra-ai-platform"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}
