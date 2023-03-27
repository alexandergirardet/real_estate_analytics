from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.docker_operator import DockerOperator

default_args = {
    'owner': 'alex',
    'retries': 5,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='rightmove_extraction_dag_test',
    default_args=default_args,
    description='This is the development dag for the rightmove extraction pipeline',
    start_date=datetime(2024, 2, 8, 2),
    schedule_interval='@daily'
) as dag:
    task1 = DockerOperator(
        # A task is an instance of an Operator
        task_id='run_rightmove_extraction',
        image='alexcessy/scrapy',
        api_version='auto',
        command='python my_scrapy_script.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='bridge',
        dag=dag,
)

task1