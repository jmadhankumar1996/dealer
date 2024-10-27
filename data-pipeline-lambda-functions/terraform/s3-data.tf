# Landing Zone S3 bucket
# Defined in dvo-provisioning
data "aws_s3_bucket" "data_pipeline_landing_zone" {
  bucket = "${var.owner}-${var.env}-landing-zone"
}
