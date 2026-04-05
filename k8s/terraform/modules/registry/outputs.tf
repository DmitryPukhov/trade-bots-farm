output "registry_url" {
  value       = "$(minikube ip):30500"
  description = "Docker registry URL"
}