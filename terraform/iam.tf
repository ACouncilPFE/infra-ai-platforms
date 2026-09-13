# Minimal-privilege IAM role for the node — CloudWatch agent access only.
# Demonstrates least-privilege thinking rather than attaching AdministratorAccess.

resource "aws_iam_role" "node" {
  name = "infra-ai-platform-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "node" {
  name = "infra-ai-platform-node-profile"
  role = aws_iam_role.node.name
}
