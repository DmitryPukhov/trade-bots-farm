from datetime import datetime

from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

with DAG(
        'run_all',
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    """ Main start DAG, triggers all batch loading and processing DAGs"""

    process_stream_full = TriggerDagRunOperator(
        task_id='trigger_process_stream_full_dag',
        trigger_dag_id='process_stream_full',
        execution_date='{{ ts }}',
    )
    process_batch_full = TriggerDagRunOperator(
        task_id='trigger_process_batch_full_dag',
        trigger_dag_id='process_batch_full',
        execution_date='{{ ts }}',
        wait_for_completion=True,  # Will wait batch here
    )

    # Trigger streams forever, then do full batch load and process, wait for batch completion
    process_stream_full >> process_batch_full
