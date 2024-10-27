##########################
# Volvo Infleet Schedule #
##########################
resource "aws_cloudwatch_event_rule" "volvo_infleet_schedule" {
  description         = "Triggers Volvo infleet Lambda based on environment schedule"
  name                = "${local.default_resource_name}-volvo-infleet-schedule"
  schedule_expression = local.schedule_expression
}

resource "aws_cloudwatch_event_target" "volvo_infleet_target" {
  arn       = module.volvo_infleet_lambda.arn
  rule      = aws_cloudwatch_event_rule.volvo_infleet_schedule.name
  target_id = "${local.default_resource_name}-volvo-infleet-target"
}

resource "aws_lambda_permission" "allow_eventbridge_to_invoke_volvo_infleet" {
  action        = "lambda:InvokeFunction"
  function_name = module.volvo_infleet_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.volvo_infleet_schedule.arn
  statement_id  = "${local.default_resource_name}-volvo-infleet-eventbridge-permission"
}