FROM apache/airflow:2.3.0-python3.9

USER root

RUN sudo apt-get update && \
    sudo apt install software-properties-common -y && \
    sudo add-apt-repository ppa:deadsnakes/ppa -y && \
    sudo apt install python3.9 -y 

RUN sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1 
RUN sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

RUN sudo apt-get remove -y python3.7
RUN sudo apt-get autoremove -y

RUN python -m pip install --upgrade pip
RUN pip3 install virtualenv

COPY scrapy_requirements.txt /scrapy_requirements.txt

USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt

RUN virtualenv venv && \
    . venv/bin/activate && \
    pip install --user -r scrapy_requirements.txt

RUN deactivate
