variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "secret_values" {
  description = "Map of secret names to maps of placeholder values. Keys should match the placeholder names in the secret definition YAML files (without braces)."
  type        = map(map(string))
  default     = {}
}