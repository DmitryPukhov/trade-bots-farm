from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.python import PythonVirtualenvOperator


def print_hello():
    print("Hello World")


def task_wrapper(**kwargs):
    task_instance = kwargs['ti']  # TaskInstance object
    task_id = task_instance.task_id
    dag_id = task_instance.dag_id
    print(f"Running dag {dag_id}, task {task_id}")

    # Load environment variables
    from dotenv import load_dotenv
    import os
    env_name = f"{task_id}.env"
    env_dir = "/opt/trade-bots-farm/environment"
    env_path = os.path.join(f"{env_dir}", f"{env_name}")
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Environment file not found at {env_path}")
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")

    # Initialize logging
    print("Configuring logging")
    import logging
    import os
    log_level = os.environ.get("LOG_LEVEL", logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s -  %(module)s.%(funcName)s:%(lineno)d  - %(levelname)s - %(message)s'
    )
    logging.info("Logging configured")

    # Start the job
    from raw_to_preproc_app import RawToPreprocApp
    RawToPreprocApp().run()


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
        'raw_to_preproc_stream',
        default_args=default_args,
        description='Transform raw data to preprocessed data',
        schedule_interval="@once",  # Run daily
        start_date=datetime(2023, 1, 1),
        catchup=False,
        tags=['trade-bots-farm'],
) as dag:
    airflow_dags_dir = "/opt/airflow/dags"
    airflow_wheels_dir = "/opt/airflow/dags/.wheels"
    run_preprocessing = PythonVirtualenvOperator(
        task_id="raw_to_preproc_stream",
        python_callable=task_wrapper,

        requirements=[
            f"--find-links={airflow_wheels_dir}",
            f"{airflow_wheels_dir}/raw_level2_preproc-0.1.0-py3-none-any.whl",
            "python-dotenv"
        ],  # or from PyPI
        op_kwargs={
            "env_vars": {
                "PYTHONPATH": f"{airflow_wheels_dir}",
                # Ensure Python knows where to write logs
                "PYTHONUNBUFFERED": "1",
                "LOG_LEVEL": "INFO"
            }
        },
        system_site_packages=False,
    )
    # Define the task
    hello_task = PythonOperator(
        task_id='print_hello',
        python_callable=print_hello,
    )

    # Set the task as the only task in the DAG
    hello_task >> run_preprocessing
