terraform {
  cloud {
    organization = "dealerware"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = local.default_tags
  }
}

provider "aws" {
  alias  = "silvercar"
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}