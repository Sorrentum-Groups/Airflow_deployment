provider "aws" {
  region = var.region
}


terraform {
  backend "s3" {
    bucket = "sorrentum-template-ec2"
    key    = "terraformstate/terraform.tfstate"
    region = "us-east-1"
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "sorrentum_template_ec2" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.large"
  vpc_security_group_ids = [aws_security_group.sorrentum_template_ec2.id]
#  key_name      = "my_devops_acct_key.pem"
  tags = {
    Name = var.tag_name
  }
}



#security group allowing http and https traffic

resource "aws_security_group" "sorrentum_template_ec2" {
  name        = "sorrentum_template_ec2"
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


