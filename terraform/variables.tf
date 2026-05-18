variable "vpc_id" {
  description = "VPC ID for the project"
  type        = string
  default     = "vpc-055b57b4906f95f03"
}

variable "subnet_id" {
  description = "Subnet ID for EC2 instances"
  type        = string
  default     = "subnet-09ae42c851723e9d3"
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
  default     = "vockey"
}

variable "repo_url" {
  description = "GitHub repository URL to clone the project"
  type        = string
  default     = "https://github.com/izqsebas-sys/proyecto-cloud.git"
}

variable "db_password" {
  description = "PostgreSQL application user password"
  type        = string
  default     = "apppassword"
  sensitive   = true
}
