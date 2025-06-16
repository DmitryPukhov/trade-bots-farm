from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from dag_tools import tbf_task_operator

# Define the DAG
task_envs = [

    # Process level2
    {"S3_SRC_DIR": "trade-bots-farm/data/raw/pytrade2/BTC-USDT/level2",
     "S3_DST_DIR": "trade-bots-farm/data/preproc/BTC-USDT/level2",
     "KIND": "level2", "TICKER": "BTC-USDT"},

    # Process candles
    {"S3_SRC_DIR": "trade-bots-farm/data/raw/pytrade2/BTC-USDT/candles",
     "S3_DST_DIR": "trade-bots-farm/data/preproc/BTC-USDT/candles",
     "KIND": "candles", "TICKER": "BTC-USDT"},
]
with DAG(
        'process_batch_raw_to_preproc',
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    # create [(source, dest, kind)] from config

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
    chain(*tasks)
