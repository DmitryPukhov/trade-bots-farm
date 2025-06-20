from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.api.client.local_client import Client
from datetime import datetime, timedelta


def stop_all_dags(**context):
    c = Client(None, None)
    dags = c.get_dags()
    for dag in dags:
        if dag.dag_id != 'stop_all_dags':  # Skip self
            c.pause_dag(dag_id=dag.dag_id)
            print(f"Paused DAG: {dag.dag_id}")

with DAG(
        'stop_all_dags',
        schedule_interval=None,
        catchup=False,
        tags=['admin'],
) as dag:

    stop_dags_task = PythonOperator(
        task_id='stop_all_dags_task',
        python_callable=stop_all_dags,
        provide_context=True,
    )