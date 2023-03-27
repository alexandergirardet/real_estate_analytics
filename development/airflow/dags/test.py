response_json = {"node_name": "889628ec664c", "status": "ok", 
                 "pending": [], 
                 "running": [{"project": "real_estate_extraction", "spider": "rightmove", "id": "6609a17ecca511eda6b40242ac180002", "start_time": "2023-03-27 13:43:49.121763", "end_time": "2023-03-27 13:47:10.005673", "log_url": "/logs/real_estate_extraction/rightmove/6609a17ecca511eda6b40242ac180002.log", "items_url": "/items/real_estate_extraction/rightmove/6609a17ecca511eda6b40242ac180002.jl"}, {"project": "real_estate_extraction", "spider": "rightmove", "id": "ae78badacca511eda6b40242ac180002", "start_time": "2023-03-27 13:45:54.200698", "end_time": "2023-03-27 13:47:22.601501", "log_url": "/logs/real_estate_extraction/rightmove/ae78badacca511eda6b40242ac180002.log", "items_url": "/items/real_estate_extraction/rightmove/ae78badacca511eda6b40242ac180002.jl"}], 
                 "finished": []}

import requests

import time

PROJECT_NAME = 'real_estate_extraction'
CURRENT_JOB = "6609a17ecca511eda6b40242ac180002"

def shut_down_jobs(jobs_to_shutdown):
    count = 0
    for job_id in jobs_to_shutdown:
        print(f'Shutting down job {job_id}')
        url = 'http://localhost:6800/cancel.json'
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
            print(f"{len(response_json['running'])} jobs are running, shutting down the non current job.")
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
    
def check_job_status(**context):

    '''
    This will allow the job to run for 5 minutes checking the status every 30 seconds, before either 
    returning the job status if it is continuing or shutting the job after 5 minutes.
    '''

    result = context['task_instance'].xcom_pull(task_ids='print_projects')

    if current_job_id:
        current_job_id = result['jobid']
        print('Job has been received. Job ID:', current_job_id)
    else:
        print("Job ID has not been received")
    
    url = 'http://localhost:6800/listjobs.json'
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
                print('Job Status returned an error')

        else:
            print(f"HTTP request failed at {time.strftime('%H:%M:%S')}")
            break
        
        print(f"HTTP request sent at {time.strftime('%H:%M:%S')}")
        time.sleep(20)
        count += 1

    if count == 10:
        print("Job running for 5 minutes, shutting down to avoid server overload")
        url = 'http://localhost:6800/cancel.json'
        data = {'project': PROJECT_NAME, 'job': current_job_id}
        response = requests.post(url, data=data)

        if response.status_code == 200:
            print("Job shut successfully")
        else:
            print("Error shutting down job")
    else:
        print("Job finished successfully")
        
        
if __name__ == '__main__':
    job_id = "65d774b6ccbd11eda6b40242ac180002"
    check_job_status(job_id)

