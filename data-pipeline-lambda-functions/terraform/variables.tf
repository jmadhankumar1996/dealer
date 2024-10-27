# Project definition tags
# Do not change the defaults since S3 bucket policies are dependent on these values

variable "env" {
  description = "Describes which environment this belongs to.  Typically one of [dev, tst, stg, prd]"
  type        = string
}

variable "owner" {
  default     = "data"
  description = "AWS Tag: Describes business-unit level Owner of these resources.  Also used as a naming prefix"
  type        = string
}

variable "product" {
  default     = "pipeline"
  description = "AWS Tag: Describes which product is associated with these resources"
  type        = string
}

variable "region" {
  default     = "us-east-1"
  description = "Region in the account which resources will be placed into"
  type        = string
}

###########################
# Project definition tags #
###########################
variable "image_tag" {
  description = "ECR image tag for the release"
  type        = string
}

variable "lambda_timeout" {
  default     = 600
  description = "Lambda timeout for event processing"
  type        = number
}
