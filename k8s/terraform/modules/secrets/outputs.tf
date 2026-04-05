output "secret_names" {
  value       = [for s in kubernetes_secret.secrets : s.metadata[0].name]
  description = "Names of deployed secrets"
}