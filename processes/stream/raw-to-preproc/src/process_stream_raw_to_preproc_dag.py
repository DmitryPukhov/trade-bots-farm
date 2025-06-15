from datetime import datetime

from airflow import DAG

from dag_tools import tbf_task_operator

# Define the DAG
with DAG(
        'process_stream_raw_to_preproc',
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    # create [(source, dest, kind)] from config

    task_envs = [
        # Process level2
        {"KAFKA_TOPIC_SRC": "raw.htx.market.btc-usdt.depth.step13", "KAFKA_TOPIC_DST": "preproc.btc-usdt.level2.1min",
         "KIND": "level2", "TICKER": "btc-usdt"},
        # Process candles
        {"KAFKA_TOPIC_SRC": "raw.htx.market.btc-usdt.kline.1min",
         "KAFKA_TOPIC_DST": "preproc.btc-usdt.candles.1min",
         "KIND": "candles", "TICKER": "btc-usdt"}
    ]

    # Create tasks list for each source,  dest, kind
    parallel_tasks = []
    for task_env in task_envs:
        task_id = f"process_stream_raw_to_preproc_{task_env["TICKER"]}_{task_env["KIND"]}"
        # Parallel process level2, candles, bid/ask if configured
        task_operator = tbf_task_operator(
            task_id=task_id,
            wheel_file_name="trade_bots_farm_process_stream_raw_to_preproc-0.1.0-py3-none-any.whl",
            module_name="process_stream_raw_to_preproc_app",
            class_name="ProcessStreamRawToPreprocApp",
            **{"env_vars": task_env})
        parallel_tasks.append(task_operator)

    # Final workflow
    parallel_tasks
