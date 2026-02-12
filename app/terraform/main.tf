terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.5.0"
    backend "s3" {
    bucket         = "cyndx-terraform-state-bhargavi"
    key            = "langgraph-api/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "cyndx-terraform-locks-bhargavi"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"
}