# Split into its own file to keep the "reliability" concern visually
# separate from provisioning — reviewers should be able to find this fast.

resource "aws_sns_topic" "alerts" {
  name = "infra-ai-platform-alerts"
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "infra-ai-platform-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Node CPU utilization above 80% for 10 minutes"
  dimensions = {
    InstanceId = aws_instance.k3s_node.id
  }
  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "status_check_failed" {
  alarm_name          = "infra-ai-platform-status-check-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 1
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "EC2 instance failed a status check"
  dimensions = {
    InstanceId = aws_instance.k3s_node.id
  }
  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "infra-ai-platform-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 2
  metric_name         = "mem_used_percent"
  namespace           = "InfraAIPlatform"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Node memory utilization above 85% for 10 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
