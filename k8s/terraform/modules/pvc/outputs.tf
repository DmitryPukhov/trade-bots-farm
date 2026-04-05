output "pvc_name" {
  value       = kubernetes_persistent_volume_claim.pvc.metadata[0].name
  description = "Name of the PVC"
}