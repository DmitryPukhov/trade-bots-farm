from datetime import datetime

from airflow import DAG
from airflow.models import DagRun
from airflow.operators.python import PythonOperator
from airflow.utils.session import create_session


def stop_all_running_dags(**context):
    with create_session() as session:
        # Get all running DAG runs (excluding this DAG)
        running_dags = session.query(DagRun).filter(
            DagRun.state == 'running',
            DagRun.dag_id != 'stop_all_running_dags'
        ).all()

        for dag_run in running_dags:
            print(f"Stopping DAG run: {dag_run.dag_id} (run_id: {dag_run.run_id})")

            # Mark the DAG run as failed (this will stop it)
            dag_run.set_state('failed')

        session.commit()

with DAG(
        'stop_all_running_dags',
        start_date=datetime(2023, 1, 1),
        schedule_interval=None,
        catchup=False,
        tags=['admin'],
) as dag:

    stop_dags_task = PythonOperator(
        task_id='stop_all_running_dags_task',
        python_callable=stop_all_running_dags,
    )