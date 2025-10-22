"""
CloudWatch Monitoring and Alerting Configuration
"""

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  count = var.alarm_email != "" ? 1 : 0
  name  = "${var.project_name}-alarms"
  
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# CloudWatch Alarm: Instance Status Check
resource "aws_cloudwatch_metric_alarm" "instance_status" {
  alarm_name          = "${var.project_name}-instance-status-check"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Asterisk instance status check failed"
  alarm_actions       = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []
  
  dimensions = {
    InstanceId = aws_instance.asterisk.id
  }
  
  tags = local.common_tags
}

# CloudWatch Alarm: CPU Utilization
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project_name}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Asterisk instance CPU utilization is too high"
  alarm_actions       = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []
  
  dimensions = {
    InstanceId = aws_instance.asterisk.id
  }
  
  tags = local.common_tags
}

# CloudWatch Alarm: Memory Utilization (requires CloudWatch agent)
resource "aws_cloudwatch_metric_alarm" "memory_high" {
  count               = var.enable_cloudwatch_monitoring ? 1 : 0
  alarm_name          = "${var.project_name}-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "mem_used_percent"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Asterisk instance memory utilization is too high"
  alarm_actions       = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []
  
  dimensions = {
    InstanceId = aws_instance.asterisk.id
  }
  
  tags = local.common_tags
}

# CloudWatch Alarm: Disk Space
resource "aws_cloudwatch_metric_alarm" "disk_space" {
  count               = var.enable_cloudwatch_monitoring ? 1 : 0
  alarm_name          = "${var.project_name}-disk-space-low"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "disk_used_percent"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Asterisk instance disk space is running low"
  alarm_actions       = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []
  
  dimensions = {
    InstanceId = aws_instance.asterisk.id
    path       = "/"
    fstype     = "xfs"
  }
  
  tags = local.common_tags
}

# Custom Metric: SIP Trunk Status
resource "aws_cloudwatch_log_metric_filter" "sip_registration_failed" {
  name           = "${var.project_name}-sip-registration-failed"
  log_group_name = aws_cloudwatch_log_group.asterisk.name
  pattern        = "[time, level=ERROR*, msg=\"*registration*failed*\"]"
  
  metric_transformation {
    name      = "SIPRegistrationFailures"
    namespace = "Asterisk/${var.project_name}"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "sip_registration" {
  alarm_name          = "${var.project_name}-sip-registration-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "SIPRegistrationFailures"
  namespace           = "Asterisk/${var.project_name}"
  period              = 300
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "Multiple SIP registration failures detected"
  alarm_actions       = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []
  treat_missing_data  = "notBreaching"
  
  tags = local.common_tags
}

# Custom Metric: Call Failures
resource "aws_cloudwatch_log_metric_filter" "call_failed" {
  name           = "${var.project_name}-call-failed"
  log_group_name = aws_cloudwatch_log_group.asterisk.name
  pattern        = "[time, level, msg=\"*Call*failed*\" || msg=\"*hangup*cause*16*\"]"
  
  metric_transformation {
    name      = "CallFailures"
    namespace = "Asterisk/${var.project_name}"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "call_failure_rate" {
  alarm_name          = "${var.project_name}-call-failure-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CallFailures"
  namespace           = "Asterisk/${var.project_name}"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "High call failure rate detected"
  alarm_actions       = var.alarm_email != "" ? [aws_sns_topic.alarms[0].arn] : []
  treat_missing_data  = "notBreaching"
  
  tags = local.common_tags
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "asterisk" {
  dashboard_name = "${var.project_name}-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", { stat = "Average", label = "CPU %" }],
            ["CWAgent", "mem_used_percent", { stat = "Average", label = "Memory %" }]
          ]
          period = 300
          region = var.aws_region
          title  = "System Resources"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["Asterisk/${var.project_name}", "SIPRegistrationFailures", { stat = "Sum" }],
            [".", "CallFailures", { stat = "Sum" }]
          ]
          period = 300
          region = var.aws_region
          title  = "SIP Trunk Health"
        }
      },
      {
        type = "log"
        properties = {
          query   = "SOURCE '${aws_cloudwatch_log_group.asterisk.name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20"
          region  = var.aws_region
          title   = "Recent Errors"
        }
      }
    ]
  })
}
