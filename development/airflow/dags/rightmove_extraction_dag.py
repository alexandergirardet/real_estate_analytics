from datetime import datetime, timedelta
import requests
import time

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException

PROJECT_NAME = 'real_estate_extraction'
SPIDER_NAME = 'rightmove'

def check_job_status(**context):

    '''
    This will allow the job to run for 5 minutes checking the status every 30 seconds, before either 
    returning the job status if it is continuing or shutting the job after 5 minutes.
    '''

    result = context['task_instance'].xcom_pull(task_ids='schedule_job_task')

    print(result)

    if result:
        current_job_id = result['jobid']
        print('Job has been received. Job ID:', current_job_id)
    else:
        print("Job ID has not been received")
        raise AirflowException('Job ID has not been received')
    
    url = 'http://scrapyd-app:6800/listjobs.json'
    params = {'project': PROJECT_NAME}

    count = 0
    while count < 10:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            response_json = response.json()
            status_dict = handle_job_status(response_json, current_job_id)
            if status_dict['status'] == 'finished':
                break
            elif status_dict['status'] == 'running':
                print('Job is still running')
            elif status_dict['status'] == 'pending':
                print('Job is pending')
            else:
                raise AirflowException('Job Status returned an error')

        else:
            print(f"HTTP request failed at {time.strftime('%H:%M:%S')}")
            break
        
        print(f"HTTP request sent at {time.strftime('%H:%M:%S')}")
        time.sleep(30)
        count += 1

    if count == 10:
        print("Job running for 5 minutes, shutting down to avoid server overload")
        url = 'http://scrapyd-app:6800/cancel.json'
        data = {'project': PROJECT_NAME, 'job': current_job_id}
        response = requests.post(url, data=data)

        if response.status_code == 200:
            print("Job shut successfully")
        else:
            print("Error shutting down job")
    else:
        print("Job finished successfully")

PROJECT_NAME = 'real_estate_extraction'
SPIDER_NAME = 'rightmove'

# Scrapy Jobs
def shut_down_jobs(jobs_to_shutdown):
    count = 0
    for job_id in jobs_to_shutdown:
        print(f'Shutting down job {job_id}')
        url = 'http://scrapyd-app:6800/cancel.json'
        data = {'project': PROJECT_NAME, 'job': job_id}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print(f"{job_id} has been shut down")
            count += 1
        else:
            print(f"{job_id} has not been shut down")

    if count == len(jobs_to_shutdown):
        return True
    else:
        return False
    
def handle_running_jobs(running_jobs, current_job_id):
    if len(running_jobs) > 1:
            print(f"{len(running_jobs)} jobs are running, shutting down the non current job.")
            jobs_to_shutdown = [job for job in running_jobs if job != current_job_id]
            shut_down_flag = shut_down_jobs(jobs_to_shutdown)
            if shut_down_flag:
                print('All non current jobs have been shut down')
            else:   
                print('Not all non current jobs have been shut down')
    else:
        if running_jobs[0] == current_job_id:
            print('Current job is running, no need to shut down.')
        else:
            print('Another job is running, shutting down non target current job.')
            shut_down_flag = shut_down_jobs(running_jobs)
            if shut_down_flag:
                print('Current non target job has been shut down')
            else:
                print('Current non target job has failed to shut down')

    
def handle_job_status(response_json, current_job_id):
    """Returns dict with job_status and handles scenarios for job status.

    Args:
        response_json (dict): JSON response from scrapyd API
        current_job_id (str): Current job id

    Returns:
        dict: Dictonary with status either with 'running', 'pending', 'finished' or 'error'
    """

    print("Current job is", current_job_id)

    running_jobs = [job['id'] for job in response_json['running']]
    pending_jobs = [job['id'] for job in response_json['pending']]
    finished_jobs = [job['id'] for job in response_json['finished']]

    if current_job_id in running_jobs:
        handle_running_jobs(running_jobs, current_job_id)

        print('Job is running')
        return {"status": "running"}
    
    elif current_job_id in pending_jobs:
        print('Job is pending')
        if len(running_jobs):
            handle_running_jobs(running_jobs, current_job_id)
        return {"status": "pending"}
    
    elif current_job_id in finished_jobs:
        print('Job is finished')
        if len(running_jobs):
            handle_running_jobs(running_jobs, current_job_id)
        return {"status": "finished"}
    
    else:
        print('Job is not in running, pending or finished')
        if len(running_jobs):
            handle_running_jobs(running_jobs, current_job_id)
        return {"status": "error"}

def schedule_job():
    """Schedules job and sends job id to Airflow as XComm.

    Returns:
        dict: Dictonary with job id as XComm
    """
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
        result = {'jobid': response_json['jobid']}
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

    task4 = PythonOperator(
        task_id='check_job_status',
        python_callable=check_job_status,
        dag=dag,
        provide_context=True,
    )

    task5 = BashOperator(
        task_id='trigger_transformation',
        bash_command='cd /app/transformation && python processor.py',
        dag=dag
)

task1 >> task2 >> task3 >> task4 >> task5