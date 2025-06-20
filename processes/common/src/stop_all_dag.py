from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import DagRun, TaskInstance
from airflow.utils.state import State
from airflow.utils.session import create_session
from datetime import datetime, timezone
import logging


def stop_all_running_dags(**context):
    with create_session() as session:
        # Get all running DAG runs (excluding this DAG)
        running_dags = session.query(DagRun).filter(
            DagRun.state == 'running',
            DagRun.dag_id != 'stop_all_running_dags'
        ).all()

        if not running_dags:
            logging.info("No running DAGs found")
            return

        for dag_run in running_dags:
            logging.info(f"Processing DAG: {dag_run.dag_id} (run_id: {dag_run.run_id})")

            # First, find and fail all running tasks
            running_tasks = session.query(TaskInstance).filter(
                TaskInstance.dag_id == dag_run.dag_id,
                TaskInstance.run_id == dag_run.run_id,
                TaskInstance.state == State.RUNNING
            ).all()

            for task in running_tasks:
                logging.info(f"  - Failing task: {task.task_id}")
                task.state = State.FAILED
                task.end_date = datetime.now(timezone.utc)

            # Then mark the DAG run as failed
            dag_run.state = State.FAILED
            dag_run.end_date = datetime.now(timezone.utc)

            session.commit()
            logging.info(f"Successfully stopped DAG: {dag_run.dag_id}")
with DAG(
        'stop_all_running_dags',
        start_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        schedule_interval=None,
        catchup=False,
        tags=['admin'],
) as dag:

    stop_dags_task = PythonOperator(
        task_id='stop_all_running_dags_task',
        python_callable=stop_all_running_dags,
    )