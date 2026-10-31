terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aiven = {
      source  = "aiven/aiven"
      version = ">= 4.0.0, < 5.0.0"
    }
  }
}

provider "aiven" {
  api_token = var.aiven_api_token
}

# PostgreSQL gratuito da Aiven (free-1-1gb: 1 CPU, 1 GB de RAM, 1 GB de disco).
# No plano gratuito a Aiven escolhe a nuvem; cloud_name registra a regiao atribuida (do-sfo).
resource "aiven_pg" "tse" {
  project                = var.aiven_project_name
  service_name           = var.service_name
  cloud_name             = var.cloud_name
  plan                   = var.plan
  termination_protection = false

  tag {
    key   = "projeto"
    value = "big-data-tse-2024"
  }

  tag {
    key   = "uso"
    value = "academico"
  }

  pg_user_config {
    pg_version = var.pg_version

    public_access {
      pg = true
    }

    ip_filter = var.ip_filter
  }
}
