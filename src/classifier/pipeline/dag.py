import datetime as dt

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

from classifier.pipeline import download, prepare, train

with DAG(
    dag_id="classifier_pipeline",
    start_date=dt.datetime(2026, 10, 12, tzinfo=dt.UTC),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    description="Скачивание КТГ, подготовка и обучение RandomForest",
) as dag:
    download_dataset = PythonOperator(
        task_id="download_dataset",
        python_callable=download.download_dataset,
        do_xcom_push=False,
    )
    prepare_dataset = PythonOperator(
        task_id="prepare_dataset",
        python_callable=prepare.prepare_dataset,
    )
    train_and_log = PythonOperator(
        task_id="train_and_log",
        python_callable=train.train_and_log,
    )
    download_dataset >> prepare_dataset >> train_and_log
