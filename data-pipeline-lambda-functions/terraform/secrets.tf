######################
# Volvo Infleet  API #
######################

# Note: Secrets with the same name can not be deleted immediately and replaced.  Reach out to CLY if
# you need to rebuild secrets.

resource "aws_secretsmanager_secret" "volvo_infleet_loaner" {
  name        = "${var.owner}/${var.env}/volvo-infleet/loaner"
  description = "Loaner API secrets for the Volvo Infleet service"
  kms_key_id  = data.aws_kms_key.data_kms_key.id
}

resource "aws_secretsmanager_secret" "volvo_infleet_order" {
  name        = "${var.owner}/${var.env}/volvo-infleet/order"
  description = "Order API secrets for the Volvo Infleet service"
  kms_key_id  = data.aws_kms_key.data_kms_key.id
}
