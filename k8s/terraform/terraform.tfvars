namespace            = "trade-bots-farm"
enable_seaweedfs     = true
enable_mlflow        = false
enable_prometheus    = false
enable_grafana       = false
enable_kafka         = false
enable_kafka_ui      = false
enable_kafka_connect = false
enable_airflow       = false
enable_registry      = false
enable_secrets       = true

seaweedfs_ingress_enabled = true
seaweedfs_ingress_host    = "seaweedfs.tradebotsfarm.minikube.cluster"
seaweedfs_s3_ingress_host = "s3.tradebotsfarm.minikube.cluster"
seaweedfs_filer_ingress_host = "filer.tradebotsfarm.minikube.cluster"
seaweedfs_master_ingress_host = "master.tradebotsfarm.minikube.cluster"