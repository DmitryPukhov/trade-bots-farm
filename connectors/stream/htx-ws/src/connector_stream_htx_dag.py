from datetime import datetime

from airflow import DAG

from dag_tools import tbf_task_operator

# Define the DAG
with (DAG(
        'connector_stream_htx',
        schedule_interval=None,  # Run daily
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag):
    tbf_task_operator(
        task_id="connector_stream_htx",
        wheel_file_name="trade_bots_farm_connector_stream_htx-0.1.0-py3-none-any.whl",
        module_name="connector_stream_htx_app",
        class_name="ConnectorStreamHtxApp")
