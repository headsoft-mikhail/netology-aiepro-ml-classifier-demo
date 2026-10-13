set dotenv-load
set dotenv-required := false

export MLFLOW_PORT := env("MLFLOW_PORT", "5001")
export JUPYTER_PORT := env("JUPYTER_PORT", "5002")
export AIRFLOW_PORT := env("AIRFLOW_PORT", "5003")

default: lock  install  lint  test

# Установить или обновить pyenv и uv через Homebrew.
setup:
    brew update
    brew install pyenv uv
    brew upgrade pyenv uv

# Установить и выбрать указанную версию Python, затем пересоздать .venv.
python version:
    if ! pyenv versions --bare | grep -qx "{{version}}"; then \
        pyenv install {{version}}; \
    fi
    pyenv local {{version}}
    pyenv rehash

    uv python pin {{version}}
    uv venv --python {{version}} --clear

# Обновить uv.lock без ручной фиксации версий зависимостей.
lock:
    uv lock --upgrade

# Установить все основные и dev-зависимости из uv.lock.
install:
    uv sync --frozen --all-extras --no-install-project --all-groups
    . ./.venv/bin/activate
    just _export_model_requirements

# Отформатировать код и выполнить статические проверки.
lint:
    uv run auto-typing-final .
    uv run ruff format .
    uv run ruff check --fix .
    uv run ty check .

# Проверить компоненты проекта и сохранить отчёты в tests.
test:
    mkdir -p "tests"
    uv run pytest --cov=classifier --cov-report=term-missing --cov-report=json:tests/coverage.json

[private]
_export_model_requirements:
    mkdir -p runtime/models/classical runtime/models/neural
    uv export --frozen --no-dev --group data --group tracking \
        --no-hashes --no-header --no-emit-project --no-annotate \
        --output-file runtime/models/classical/requirements.txt > /dev/null
    uv export --frozen --no-dev --group data --group neural --group tracking \
        --no-hashes --no-header --no-emit-project --no-annotate \
        --output-file runtime/models/neural/requirements.txt > /dev/null

api:
    uv run --group service python -m classifier.api

# Поднять Airflow и выполнить все задачи DAG.
pipeline: _export_model_requirements mlflow-start
    #!/usr/bin/env bash
    set -e
    mkdir -p runtime/airflow
    docker build -f Dockerfile.airflow -t classifier-airflow .
    docker rm -f classifier-airflow 2>/dev/null || true
    trap 'docker rm -f classifier-airflow >/dev/null 2>&1 || true' EXIT
    docker run -d --name classifier-airflow --env-file .env \
        -e MLFLOW_HOST=host.docker.internal \
        -p "127.0.0.1:$AIRFLOW_PORT:8080" \
        -v "$PWD/src:/opt/project/src:ro" \
        -v "$PWD/runtime:/opt/project/runtime" \
        -v "$PWD/runtime/airflow:/opt/airflow" \
        classifier-airflow
    docker exec classifier-airflow timeout 120 bash -c \
        'until curl -fsS http://127.0.0.1:8080/api/v2/monitor/health >/dev/null 2>&1; do sleep 1; done'
    docker exec classifier-airflow python -m classifier.pipeline

# Запустить MLflow в фоне. Настройки берутся из .env.
mlflow-start:
    #!/usr/bin/env bash
    set -e
    if lsof -tiTCP:"$MLFLOW_PORT" -sTCP:LISTEN >/dev/null; then
        echo "Порт $MLFLOW_PORT уже занят — повторный запуск пропущен"
        exit 0
    fi
    mkdir -p "runtime/mlflow/artifacts"
    nohup uv run --group tracking mlflow server \
        --backend-store-uri "sqlite:///runtime/mlflow/mlflow.db" \
        --artifacts-destination "runtime/mlflow/artifacts" \
        --serve-artifacts --host 127.0.0.1 --port "$MLFLOW_PORT" --workers 1 \
        --allowed-hosts "localhost:*,127.0.0.1:*,host.docker.internal:*" \
        > "runtime/mlflow/logs.log" 2>&1 < /dev/null &
    echo "MLflow: http://127.0.0.1:$MLFLOW_PORT — запуск в фоне, лог: runtime/mlflow/logs.log"

# Остановить процесс, слушающий настроенный порт MLflow.
mlflow-stop:
    lsof -tiTCP:"$MLFLOW_PORT" -sTCP:LISTEN | xargs kill 2>/dev/null || true

# Служебные файлы Jupyter и библиотек сохраняются в рабочей папке.
jupyter-start:
    mkdir -p "runtime/jupyter" "runtime/jupyter/ipython"
    JUPYTER_RUNTIME_DIR="$PWD/runtime/jupyter" \
        IPYTHONDIR="$PWD/runtime/jupyter/ipython" \
        MLFLOW_TRACKING_URI="http://127.0.0.1:$MLFLOW_PORT" \
        nohup uv run --group research --group tracking jupyter lab \
        --ip 127.0.0.1 --port "$JUPYTER_PORT" --ServerApp.port_retries=0 \
        > "runtime/jupyter/logs.log" 2>&1 < /dev/null &

# Остановить процесс, слушающий настроенный порт Jupyter.
jupyter-stop:
    lsof -tiTCP:"$JUPYTER_PORT" -sTCP:LISTEN | xargs kill 2>/dev/null || true
