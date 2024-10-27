data "aws_kms_key" "data_kms_key" {
  key_id = "alias/${var.owner}/${var.env}"
}