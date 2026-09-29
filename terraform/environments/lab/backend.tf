terraform {
  backend "s3" {
    bucket       = "secure-gitops-platform-tfstate-950165721116"
    key          = "eks/lab/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}
