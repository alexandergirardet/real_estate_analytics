FROM apache/airflow:2.3.0-python3.9

USER root

# Copy requirements files
COPY requirements.txt /requirements.txt

# Install app for transformation
COPY app /app

# Install Airflow requirements
USER airflow
RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r /requirements.txt