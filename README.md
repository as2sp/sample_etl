# sample_etl
Тестовое задание

Общее описание системы и обработки данных с использованием Docker Compose, Spark, Hadoop и PostgreSQL

Docker Compose конфигурация:
    В файле docker-compose.yml определены сервисы, включая Apache Spark, Hadoop, PostgreSQL и API сервис.
    Каждый сервис настроен на своем соответствующем порту внутри среды Docker, а также имеет свое уникальное имя, позволяющее другим 
	контейнерам обращаться к нему.

API сервис:
    Flask API сервис запущен на отдельном контейнере с Python Slim образом.
    API предоставляет эндпоинты для добавления событий и запросов аналитических данных.

Добавление событий:
    При отправке POST-запроса на /event, данные события принимаются API сервисом.
    Затем данные передаются в PySpark, где создается DataFrame из JSON-данных события.
    DataFrame сохраняется в таблицу "events" в витрину на PostgreSQL через Spark JDBC connector.

Запрос аналитических данных:
    При отправке GET-запроса на /analytics/query, API сервис принимает параметры запроса.
    PySpark обрабатывает запрос, выполняя соответствующие операции с данными в Hadoop и Spark, используя таблицы и временные представления.
    Результаты анализа могут быть сохранены обратно в PostgreSQL или возвращены напрямую через API.

Хранение данных:
    Данные хранятся в Hadoop Distributed File System (HDFS) с доступом к ним через Hadoop Namenode и Datanode контейнеры.
    Результаты обработки и анализа данных сохраняются в PostgreSQL в виде таблиц или представлени.

Замечания и предложения: предполагается, что обработанные данные помещаются в реляционную СУБД для ускорения выборки и запросов к ним.
Если планируется использование аналитиками данных преимущественно в режиме чтения, а также объемы данных станут существенно
большими, то предлагается замменить PostgreSQL другой СУБД, предназначенной для BigData. Для простоты миграции с PostgreSQL можно
рассматривать Greenplum. Если предполагается экономия на аппаратной составляющей, то оптимальнее будет Clickhouse.
В любом случае, как последний этап ETL процесса, СУБД с витриной меняется достаточно просто. Для этого необходимо внести изменения
в docker_compose.yaml в части замены PostgreSQL. Например, для Greenplum:
greenplum:
    image: 'greenplum/greenplum-database:latest'
    ports:
      - '5432:5432'
    environment:
      - GP_PASSWORD=mypass

и в секции API:
depends_on:
      - spark-master
      - greenplum

Аналогично с Clickhouse:
clickhouse-server:
    image: 'yandex/clickhouse-server'
    ports:
      - '8123:8123'
      - '9000:9000'

и в секции API:
depends_on:
      - spark-master
      - clickhouse-server

Также, если предполагается осуществлять ETL процесс на постоянно основе, то рекомендуется включить в инфраструктуру оркестратор, например, Apache Airflow:
Для этого нужно будет добавить в docker-compose секцию:
airflow:
    image: 'apache/airflow:2.1.0'
    restart: always
    depends_on:
      - postgres
      - spark-master
      - clickhouse-server
    environment:
      - AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__LOGGING__REMOTE_LOGGING=True
      - AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=s3://your-remote-bucket/logs
      - AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID=aws_logs
      - AIRFLOW__LOGGING__LOGGING_LEVEL=INFO
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins

Вот пример DAG'а Airflow для обработки запросов через API:

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2022, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def call_api():
    response = requests.get('http://api:8000/data/update')
    # Обработка ответа, если это необходимо
    return response.status_code

with DAG('api_processing_dag', default_args=default_args, schedule_interval='@daily') as dag:
    process_api_data = PythonOperator(
        task_id='process_api_data',
        python_callable=call_api
    )

process_api_data
