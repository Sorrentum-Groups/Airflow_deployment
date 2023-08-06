# Configure the AWS Provider
provider "aws" {
  region = var.region
}
terraform {
  backend "s3" {
    bucket = "my-aws-airflow"
    key    = "terraformstate/terraform.tfstate"
    region = "us-east-1"
  }
}

# Configuration template for ec2 instance

resource "aws_instance" "sorrentum_instance" {
  ami                    = var.ami
  instance_type          = "t3.large"
  count                  = 1
  vpc_security_group_ids = [aws_security_group.sg_sorrentum.id]
  key_name               = "my_devops_acct_key"
  user_data              = file("./sorrentun_airflow.sh")

  tags = {
    Name = "sorrentum_airflow_server"
  }
}

#security group allowing http and https traffic

resource "aws_security_group" "sg_sorrentum" {
  name        = "sg_sorrentum"
  description = "Allow inbound http and https traffic"

  ingress {
    description = "http from VPC"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "https from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

ingress {
    description = "ssh from VPC"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "ssh from VPC"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }


  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }


  tags = {
    Name = "allow_http_https"
  }
} 