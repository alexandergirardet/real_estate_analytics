import psycopg2

conn = psycopg2.connect(
            host="localhost",
            database="rightmove_development",
            port=5433) # Port 5432 is already in use by the airflow container

cursor = conn.cursor()