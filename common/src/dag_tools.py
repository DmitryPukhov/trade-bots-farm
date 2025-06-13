import os

from airflow.operators.python import PythonVirtualenvOperator


def tbf_task_operator(task_id, wheel_file_name, module_name, class_name, **kwargs):
    """ PythonVirtualEnvOperator wrapper to run trade bots farm dag task.
    This method is called from dag to create the task
    Written in functional style to be compatible with PythonVirtualenvOperator callable
    """

    def tbf_task_callable(module_name, class_name, **kwargs):
        """ This callable is passed to PythonVirtualenvOperator"""

        def load_env(dag_id: str):
            """
            Load environment variables from .env file
            This method is called from dag task in PythonVirtualenvOperator
            """

            import os
            # Load environment variables
            from dotenv import load_dotenv
            env_name = f"{dag_id}.env"
            env_dir = "/opt/trade-bots-farm/environment"
            env_path = os.path.join(f"{env_dir}", f"{env_name}")
            if not os.path.exists(env_path):
                raise FileNotFoundError(f"Environment file not found at {env_path}")
            load_dotenv(env_path)
            #  env_vars came from dag and override those from .env file
            os.environ.update(kwargs.get("env_vars"))
            print(f"Loaded environment variables from {env_path} file and passed env_vars: {kwargs.get('env_vars') or {}}")

        def init_log():
            print("Configuring logging")
            import logging
            import os
            log_level = os.environ.get("LOG_LEVEL", logging.INFO)
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s -  %(module)s.%(funcName)s:%(lineno)d  - %(levelname)s - %(message)s'
            )
            logging.info("logging.error() test")
            logging.warning("logging.warning() test")
            logging.info("logging.info() test")
            logging.debug("logging.debug() test")

        import os
        task_id = os.getenv("AIRFLOW_CTX_TASK_ID")
        dag_id = os.getenv("AIRFLOW_CTX_DAG_ID")
        print(f"Running dag {dag_id}, task {task_id}")  # logging is not available here, so print is used
        # Initialization
        load_env(dag_id)
        init_log()

        # Start the job
        import importlib
        import logging
        logging.info(f"Importing {module_name}.{class_name}")
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        cls().run()

    ################# Main #################
    """ PythonVirtualenvOperator wrapper to run trade bots farm dag task."""
    airflow_wheels_dir = os.getenv("AIRFLOW_WHEELS_DIR") or "/opt/trade-bots-farm/wheels"
    return PythonVirtualenvOperator(
        task_id=task_id,
        python_callable=tbf_task_callable,
        requirements=[
            f"--find-links={airflow_wheels_dir}",
            os.path.join(airflow_wheels_dir, wheel_file_name),
            "python-dotenv"
        ],  # or from PyPI
        op_kwargs={
            "module_name": module_name,
            "class_name": class_name,
            "env_vars": {**(kwargs.get("env_vars") or {}),
                         **{
                             "PYTHONPATH": f"{airflow_wheels_dir}",
                             # Ensure Python knows where to write logs
                             "PYTHONUNBUFFERED": "1",
                             # "LOG_LEVEL": "INFO"
                         }}
        },
        system_site_packages=False,
    )
