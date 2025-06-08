from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.models.baseoperator import chain

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
        'process_batch_raw_to_preproc',
        default_args=default_args,
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
) as dag:
    # create [(source, dest, kind)] from config
    task_envs = [
        # Process candles
        {"S3_SRC_DIR": "trade-bots-farm/data/raw/pytrade2/BTC-USDT/candles",
         "S3_DST_DIR": "trade-bots-farm/data/preproc/BTC-USDT/candles",
         "KIND": "candles", "TICKER": "BTC-USDT"},

        # Process level2
        {"S3_SRC_DIR": "trade-bots-farm/data/raw/pytrade2/BTC-USDT/level2",
         "S3_DST_DIR": "trade-bots-farm/data/preproc/BTC-USDT/level2",
         "KIND": "level2", "TICKER": "BTC-USDT"},
    ]


    # Create tasks list for each source,  dest, kind
    tasks = []
    for task_env in task_envs:
        task_id = f"process_batch_raw_to_preproc_{task_env["TICKER"]}_{task_env["KIND"]}"
        # Parallel process level2, candles, bid/ask if configured
        task_operator = tbf_task_operator(
            task_id=task_id,
            wheel_file_name="trade_bots_farm_process_batch_raw_to_preproc-0.1.0-py3-none-any.whl",
            module_name="process_batch_raw_to_preproc_app",
            class_name="ProcessBatchRawToPreprocApp",
            **{"env_vars": task_env})
        tasks.append(task_operator)

    # Final workflow
    #EmptyOperator(task_id="start") >> parallel_tasks
    chain(*tasks)
