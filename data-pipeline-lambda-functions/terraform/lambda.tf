module "volvo_infleet_lambda" {
  source  = "app.terraform.io/dealerware/lambda/tf"
  version = "2.0.5"

  description = "Lambda to obtain Volvo infleet data"
  name        = "volvo-infleet"

  handler            = "lambda_function.lambda_handler"
  image_uri          = "${local.silvercar_account_id}.dkr.ecr.${var.region}.amazonaws.com/${local.ecr_repo}:volvo-infleet-${var.image_tag}"
  memory_size        = 512
  security_group_ids = []
  timeout            = var.lambda_timeout
  type               = "image"

  # Additional permissions for the infleet lambda function
  additional_policies_as_list = [
    {
      actions = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ]
      effect = "Allow"
      resources = [
        aws_secretsmanager_secret.volvo_infleet_loaner.id,
        aws_secretsmanager_secret.volvo_infleet_order.id
      ]
    },
    {
      actions   = ["kms:Decrypt"]
      effect    = "Allow"
      resources = [data.aws_kms_key.data_kms_key.arn]
    },
    {
      actions = [
        "s3:*Object",
        "s3:ListBucket"
      ]
      effect = "Allow"
      resources = [
        "${data.aws_s3_bucket.data_pipeline_landing_zone.arn}",
        "${data.aws_s3_bucket.data_pipeline_landing_zone.arn}/*"
      ]
    }
  ]

  variables = {
    ENV                  = var.env
    LZ_BUCKET            = data.aws_s3_bucket.data_pipeline_landing_zone.bucket
    TARGET_DIR           = local.volvo_infleet_dir
    VOLVO_INFLEET_LOANER = aws_secretsmanager_secret.volvo_infleet_loaner.name
    VOLVO_INFLEET_ORDER  = aws_secretsmanager_secret.volvo_infleet_order.name
  }

  env     = var.env
  owner   = var.owner
  product = var.product
  region  = var.region
}
