from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.time_delta import TimeDeltaSensor

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

    # Add a sleep before a batch to be sure that external s3 data are ready
    sleep_minutes = int(Variable.get("sleep_before_batch_minutes", default_var=5))
    sleep_task_id = f'sleep_before_batch_{sleep_minutes}_minutes'
    sleep_task = TimeDeltaSensor(
        task_id=sleep_task_id,
        delta=timedelta(minutes=sleep_minutes),  # Use param or default
    )

    process_batch_full = TriggerDagRunOperator(
        task_id='trigger_process_batch_full_dag',
        trigger_dag_id='process_batch_full',
        execution_date='{{ ts }}',
        wait_for_completion=True,  # Will wait batch here
    )

    # Trigger streams forever, wait for external s3 data ready then do full batch load and process, wait for batch completion
    process_stream_full >> sleep_task >> process_batch_full
