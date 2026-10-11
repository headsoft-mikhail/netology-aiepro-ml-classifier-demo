set dotenv-load
set dotenv-required := false

export MLFLOW_PORT := env("MLFLOW_PORT", "5001")
export JUPYTER_PORT := env("JUPYTER_PORT", "5002")

default: lock  install  lint  test

# .env автоматически читается just при наличии (set dotenv-load).
_import_env:

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

# Отформатировать код и выполнить статические проверки.
lint:
    uv run auto-typing-final .
    uv run ruff format .
    uv run ruff check --fix .
    uv run ty check .

# Проверить компоненты проекта и сохранить отчёты в tests.
test: _import_env
    mkdir -p "tests"
    uv run pytest --cov=classifier --cov-report=term-missing --cov-report=json:tests/coverage.json

# Скачать оригинал: отдельный скрипт, без подготовки данных.
fetch_dataset: _import_env
    uv run python -m classifier.data.download

# Запустить MLflow в фоне. Настройки берутся из .env.
mlflow-start: _import_env
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
        > "runtime/mlflow/logs.log" 2>&1 < /dev/null &
    echo "MLflow: http://127.0.0.1:$MLFLOW_PORT — запуск в фоне, лог: runtime/mlflow/logs.log"

mlflow-logs: _import_env
    tail -f "runtime/mlflow/logs.log"

# Остановить процесс, слушающий настроенный порт MLflow.
mlflow-stop: _import_env
    lsof -tiTCP:"$MLFLOW_PORT" -sTCP:LISTEN | xargs kill 2>/dev/null || true

# Служебные файлы Jupyter и библиотек сохраняются в рабочей папке.
jupyter-start: _import_env
    mkdir -p "runtime/jupyter" "runtime/jupyter/ipython"
    JUPYTER_RUNTIME_DIR="$PWD/runtime/jupyter" IPYTHONDIR="$PWD/runtime/jupyter/ipython" MLFLOW_TRACKING_URI="http://127.0.0.1:$MLFLOW_PORT" nohup uv run --group research --group tracking jupyter lab --ip 127.0.0.1 --port "$JUPYTER_PORT" --ServerApp.port_retries=0 > "runtime/jupyter/logs.log" 2>&1 < /dev/null &
    @echo "Jupyter: запуск в фоне, ссылка с токеном — в runtime/jupyter/logs.log"

# Остановить процесс, слушающий настроенный порт Jupyter.
jupyter-stop: _import_env
    lsof -tiTCP:"$JUPYTER_PORT" -sTCP:LISTEN | xargs kill 2>/dev/null || true
