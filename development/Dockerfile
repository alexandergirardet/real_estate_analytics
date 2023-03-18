FROM apache/airflow:2.3.0

USER root

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update

RUN apt-get install -y python3.9

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

RUN python -m pip install --upgrade pip

USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt
