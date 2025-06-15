from datetime import datetime

from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

with DAG(
        'process_batch_full',
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    """ Main batch DAG, triggers all batch loading and processing DAGs"""

    trigger_connector_batch_s3_external_dag = TriggerDagRunOperator(
        task_id='trigger_connector_batch_s3_external_dag',
        trigger_dag_id='connector_batch_s3_external',
        execution_date='{{ ts }}',
        wait_for_completion=True,  # Will wait here
    )
    trigger_process_batch_raw_to_preproc_dag = TriggerDagRunOperator(
        task_id='trigger_process_batch_raw_to_preproc_dag',
        trigger_dag_id='process_batch_raw_to_preproc',
        execution_date='{{ ts }}',
        wait_for_completion=True,  # Will wait here
    )

    trigger_connector_batch_s3_external_dag >> trigger_process_batch_raw_to_preproc_dag
