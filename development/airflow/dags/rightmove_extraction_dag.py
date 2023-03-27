from datetime import datetime, timedelta
import time
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.operators.python import PythonOperator

import requests

PROJECT_NAME = 'real_estate_extraction'
SPIDER_NAME = 'rightmove'

def schedule_job():
    # Send a CURL command to http://scrapyd-app:6800/
    url = 'http://scrapyd-app:6800/schedule.json'

    data = {
        'project': PROJECT_NAME,
        'spider': SPIDER_NAME
    }

    response = requests.post(url, data=data)

    response_json = response.json()

    print("This is the response:", response_json)

    if response_json['status'] == 'ok':
        print('Job scheduled successfully')
        result = {'jobid': response_json['job_id']}
        return result
    else:
        print('Job failed to schedule')
        return None

default_args = {
    'owner': 'alex',
    'retries': 5,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='rightmove_extraction_dag',
    default_args=default_args,
    description='This is the development dag for the rightmove extraction pipeline',
    start_date=datetime(2023, 3, 24, 2),
    schedule_interval='@daily'
) as dag:
    task1 = BashOperator(
        task_id='print_projects',
        bash_command='curl http://scrapyd-app:6800/listprojects.json',
        dag=dag
)

    task2 = BashOperator(
        task_id='print_spiders',
        bash_command=' curl http://scrapyd-app:6800/listspiders.json?project=real_estate_extraction',
        dag=dag
)

    task3 = PythonOperator(
        task_id='schedule_job_task',
        python_callable=schedule_job,
        dag=dag
    )

task1 >> task2 >> task3


import requests
import time

def check_job_status(**context):

    '''
    This will allow the job to run for 5 minutes checking the status every 30 seconds, before either 
    returning the job status if it is continuing or shutting the job after 5 minutes.
    '''

    result = context['task_instance'].xcom_pull(task_ids='print_projects')

    if result:
        job_id = result['jobid']
        print('Job has been received. Job ID:', job_id)
    else:
        print("Job ID has not been received")
        return None
    
    url = 'http://localhost:6800/listjobs.json'
    params = {'project': PROJECT_NAME}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        response_json = response.json()
        print('Jobs received successfully')
        print(response_json)


    count = 0
    while count < 10:
        response = requests.get(url)
        print(f"HTTP request sent at {time.strftime('%H:%M:%S')}")
        time.sleep(30)
        count += 1