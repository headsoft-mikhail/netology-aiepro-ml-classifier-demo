import subprocess

if __name__ == "__main__":
    subprocess.run(["airflow", "dags", "test", "classifier_pipeline"], check=True)  # noqa: S607
