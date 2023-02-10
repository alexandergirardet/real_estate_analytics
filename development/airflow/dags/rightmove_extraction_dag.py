from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'alex',
    'retries': 5,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='rightmove_extraction_dag',
    default_args=default_args,
    description='This is the development dag for the rightmove extraction pipeline',
    start_date=datetime(2023, 2, 8, 2),
    schedule_interval='@daily'
) as dag:
    task1 = BashOperator(
        # A task is an instance of an Operator
        task_id='get_token',
        bash_command="cd /app && ./script.sh "
    )

    task2 = BashOperator(
        task_id='remove_token',
        bash_command="cd /app && ./remove_token.sh "
    )

    # task3 = BashOperator(
    #     task_id='third_task',
    #     bash_command="echo hello world, this is the third task, running at the same time as task 2"
    # )

    # task1.set_downstream(task2)
    # task1.set_downstream(task3)

    # task1 >> task2
    # task >> task3

    task1 >> task2
