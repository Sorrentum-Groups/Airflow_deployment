#source "aws_vpc" "sorrentum_vpc" {
#   cidr_block       = "10.0.0.0/16"
#   instance_tenancy = "default"

#   tags = {
#     Name = "aws-sorrentum-vpc"
#   }
# }
# resource "aws_subnet" "private_1" {
#   vpc_id            = aws_vpc.sorrentum_vpc.id
#   cidr_block        = "10.0.1.0/24"
#   availability_zone = "us-east-1a"

#   tags = {
#     Name = "aws-sorrentum-subnet-1"
#   }
# }
# resource "aws_subnet" "private_2" {
#   vpc_id            = aws_vpc.sorrentum_vpc.id
#   cidr_block        = "10.0.2.0/24"
#   availability_zone = "us-east-1b"

#   tags = {
#     Name = "aws-sorrentum-subnet-2"
#   }
# }

# # Security group for sorrentum instance to allow traffic in and out of the server

# resource "aws_security_group" "sg_sorrentum" {
#   name        = "sg_sorrentum"
#   description = "Allow inbound http and https traffic"

#   ingress {
#     description = "http from VPC"
#     from_port   = 80
#     to_port     = 80
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   ingress {
#     description = "https from VPC"
#     from_port   = 443
#     to_port     = 443
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }


#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   tags = {
#     Name = "allow_http_https"
#   }
# }