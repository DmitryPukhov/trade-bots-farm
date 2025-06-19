from datetime import datetime

from airflow import DAG

from dag_tools import tbf_task_operator

with DAG(
        'process_stream_features_multi_indi',
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    """ Calculate multi indicator features from candles and level2"""

    task_id = f"process_stream_features_multi_indi_btc_usdt"
    task_operator = tbf_task_operator(
        task_id=task_id,
        wheel_file_name="trade_bots_farm_process_stream_features-0.1.0-py3-none-any.whl",
        module_name="stream_features_app",
        class_name="StreamFeaturesApp")
