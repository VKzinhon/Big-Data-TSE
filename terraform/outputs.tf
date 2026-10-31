output "postgresql_service_uri" {
  description = "URI de conexao do PostgreSQL. O valor e sensivel."
  value       = aiven_pg.tse.service_uri
  sensitive   = true
}

output "postgresql_service_host" {
  description = "Host do PostgreSQL."
  value       = aiven_pg.tse.service_host
  sensitive   = true
}

output "postgresql_service_port" {
  description = "Porta do PostgreSQL."
  value       = aiven_pg.tse.service_port
}
