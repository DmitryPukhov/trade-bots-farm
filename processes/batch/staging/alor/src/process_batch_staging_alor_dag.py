from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain

from dag_tools import tbf_task_operator

config = {"S3_SRC_DIR": "trade-bots-farm/data/raw/alor",
          "S3_DST_DIR": "trade-bots-farm/data/staging/alor",
          "TICKERS": ["MOEX.TQBR.SBER"]}

with DAG(
        'process_batch_staging_alor',
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    # create [(source, dest, kind)] from config

    # Create tasks list for each source,  dest, kind
    tasks = []
    kinds = ["level2", "candles.1min", "bid_ask"]
    tickers = config["TICKERS"]

    for ticker in tickers:
        for kind in kinds:
            # Prepare environment for task like MOEX.TQBR.SBER level2
            task_env = {key: value for key, value in config.items() if key not in ["TICKERS"]}
            task_env["TICKER"] = ticker
            task_env["KIND"] = kind

            task_id = f"process_batch_pytrade2_staging_{ticker}_{kind}"
            # Parallel process level2, candles, bid/ask if configured
            task_operator = tbf_task_operator(
                task_id=task_id,
                wheel_file_name="trade_bots_farm_process_batch_staging_alor-0.1.0-py3-none-any.whl",
                module_name="process_batch_pytrade2_staging_alor_app",
                class_name="ProcessBatchStagingAlorApp",
                **{"env_vars": task_env})
            tasks.append(task_operator)

    # Final workflow
    chain(*tasks)
