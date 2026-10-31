variable "aiven_api_token" {
  description = "Token pessoal da Aiven. Nao commitar o valor."
  type        = string
  sensitive   = true
}

variable "aiven_project_name" {
  description = "Nome do projeto na Aiven."
  type        = string
  default     = "cauamaia488-ead4"
}

variable "service_name" {
  description = "Nome do servico PostgreSQL."
  type        = string
  default     = "pg-1f18e561"
}

variable "cloud_name" {
  description = "Regiao do servico. No plano gratuito e a que a Aiven atribuiu."
  type        = string
  default     = "do-sfo"
}

variable "plan" {
  description = "Plano da Aiven. free-1-1gb e o gratuito."
  type        = string
  default     = "free-1-1gb"
}

variable "pg_version" {
  description = "Versao do PostgreSQL."
  type        = string
  default     = "18"
}

variable "ip_filter" {
  description = "IPs liberados para conexao."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}
