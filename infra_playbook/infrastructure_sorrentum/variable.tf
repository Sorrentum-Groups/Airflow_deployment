variable "region" {
  type      = string
  sensitive = true
}

variable "ami" {
  type      = string
  sensitive = true
}

#variable "ami_ie" {
#type = list
#default = ["255255552", "3553553", "355355"]
#}

locals {
  taco = {
    ami    = var.ami
    region = var.region

  }
}