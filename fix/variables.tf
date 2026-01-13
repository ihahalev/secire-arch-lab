variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_id" {
  type        = string
  description = "VPC where SG will be created"
}

variable "allowed_ingress_cidrs" {
  type        = list(string)
  description = "Allowlist for inbound 443. Do NOT use 0.0.0.0/0 in production."
  default     = []
}
