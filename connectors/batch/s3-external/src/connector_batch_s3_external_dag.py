from datetime import datetime, timedelta

import airflow
from airflow import DAG

from dag_tools import tbf_task_operator

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),

}

# Define the DAG
with DAG(
        'connector_batch_s3_external',
        default_args=default_args,
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    external_bucket = "pytrade2"
    internal_bucket = "trade-bots-farm"
    task_envs = [
        # Process level2
        {"SRC_S3_DIR": f"{external_bucket}/data/raw/level2",
         "DST_S3_DIR": f"{internal_bucket}/data/raw/pytrade2/BTC-USDT/level2",
         "TICKER": "BTC-USDT", "KIND": "level2"},
        {"SRC_S3_DIR": f"{external_bucket}/data/raw/candles",
         "DST_S3_DIR": f"{internal_bucket}/data/raw/pytrade2/BTC-USDT/candles",
         "TICKER": "BTC-USDT", "KIND": "candles"},
    ]

    tasks = []
    for task_env in task_envs:
        tasks.append(tbf_task_operator(
            task_id=f"connector_batch_s3_external_{task_env["TICKER"]}_{task_env["KIND"]}",
            wheel_file_name="trade_bots_farm_connector_batch_s3_external-0.1.0-py3-none-any.whl",
            module_name="connector_batch_s3_external_app",
            class_name="ConnectorBatchS3ExternalApp",
            **{"env_vars": task_env}
        ))

    # Run as task1 >> task2 >> ...
    airflow.models.baseoperator.chain(*tasks)
