variable "vpc_id" {
  description = "VPC ID for the project"
  type        = string
  default     = "vpc-0db51e24b1be9bc68"
}

variable "subnet_id" {
  description = "Subnet ID for EC2 instances"
  type        = string
  default     = "subnet-0a279d9c60a8ef4e0"
}

variable "ami_id" {
  description = "Amazon Linux 2023 AMI ID"
  type        = string
  default     = "ami-02dfbd4ff395f2a1b"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "EC2 key pair name"
  type        = string
  default     = "callanor2026_02_iot"
}

variable "repo_url" {
  description = "GitHub repository URL to clone the project"
  type        = string
  default     = "https://github.com/YOUR_USER/YOUR_REPO.git"
}

variable "db_password" {
  description = "PostgreSQL application user password"
  type        = string
  default     = "apppassword"
  sensitive   = true
}
