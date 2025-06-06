from datetime import datetime, timedelta

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
        'process_stream_raw_to_preproc',
        default_args=default_args,
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
) as dag:
    tbf_task_operator(
        task_id="process_stream_raw_to_preproc",
        wheel_file_name="trade_bots_farm_process_stream_raw_to_preproc-0.1.0-py3-none-any.whl",
        module_name="process_stream_raw_to_preproc_app",
        class_name="ProcessStreamRawToPreprocApp")
