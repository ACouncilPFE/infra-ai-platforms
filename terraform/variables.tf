variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name, used in tags"
  type        = string
  default     = "portfolio-demo"
}

variable "instance_type" {
  description = "EC2 instance type — kept to free-tier-eligible sizes"
  type        = string
  default     = "t3.medium"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to SSH into the node. Set to your own IP/32 — never leave this as 0.0.0.0/0 in anything real."
  type        = string
  default     = "0.0.0.0/0" # override via terraform.tfvars with your IP
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}
