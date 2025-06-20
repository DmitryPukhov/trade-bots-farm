from datetime import datetime

from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

with DAG(
        'process_stream_full',
        schedule_interval=None,
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
        max_active_runs=1
) as dag:
    """ Main stream DAG, triggers all stream loading and processing DAGs"""

    # Stream child dags
    connector_stream_htx = TriggerDagRunOperator(
        task_id='trigger_connector_stream_htx_dag',
        trigger_dag_id='connector_stream_htx',
        execution_date='{{ ts }}',
        wait_for_completion=False,  # Will wait here
    )
    process_stream_raw_to_preproc = TriggerDagRunOperator(
        task_id='trigger_process_stream_raw_to_preproc_dag',
        trigger_dag_id='process_stream_raw_to_preproc',
        execution_date='{{ ts }}',
        wait_for_completion=False,  # Will wait here
    )
    process_stream_features_multi_indi = TriggerDagRunOperator(
        task_id='trigger_process_stream_features_multi_indi_dag',
        trigger_dag_id='process_stream_features_multi_indi',
        execution_date='{{ ts }}',
        wait_for_completion=False,  # Will wait here
    )

    # Full batch load and process cycle
    process_batch_full = TriggerDagRunOperator(
        task_id='trigger_process_batch_full_dag',
        trigger_dag_id='process_batch_full',
        execution_date='{{ ts }}',
        wait_for_completion=False,  # Will wait here
    )

    # Start stream processing, then run batch processing
    [connector_stream_htx, process_stream_raw_to_preproc, process_stream_features_multi_indi] >> process_batch_full
