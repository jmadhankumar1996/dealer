locals {
  naming_pattern        = [var.owner, var.env, var.product]
  default_resource_name = trim(substr(join("-", local.naming_pattern), 0, 40), "-") # Strip the name to max of 40 characters, remove trailing dashes
  ecr_repo              = "data/pipeline-lambda-functions"
  silvercar_account_id  = "377621159926"
  schedule_expression   = var.env == "tst" ? "cron(0 14 * * ? *)" : "cron(0 6 * * ? *)" # conditional schedule expression if var.env is tst, and if true, runs at 14PM UTC (8AM CST). Otherwise, it uses cron(0 6 * * ? *) (which runs at 6 AM UTC (12AM CST)).
  volvo_infleet_dir     = "data/infleet/volvo/${var.env}/"

  default_tags = {
    Domain      = var.owner # preparing for the future when we use domain instead of owner for tags
    Environment = var.env
    Managed     = "terraform"
    Owner       = var.owner
    Product     = var.product
  }
}