# CTG classifier demo

Выполнены EDA, подготовка данных, обучение и подбор классических и нейросетевых классификаторов для CLASS и NSP. В сервисе используются оптимизированные RandomForest для CLASS и NSP; MLP остаётся сравнением в исследованиях. Подготовка и обучение выполняются через Airflow. FastAPI принимает признаки, классифицирует фиксированные демопримеры и сохраняет исследования в SQLite. Frontend и автоматический поток — следующие этапы.

## Запуск

Python проекта — 3.14.7; версия закреплена в `.python-version` и `pyproject.toml`.

Из корня проекта, без ручной активации окружения и переменных перед командами:

```bash
just lock
just install
just mlflow-start
just jupyter-start
```

Базовые команды скопированы из netology-aiagnt. `just lock` выполняет `uv lock --upgrade`; `just install` устанавливает все группы в отдельную `.venv`. Форматирование и проверки входят в `just lint`. Тесты — `just test`.

## Группы зависимостей

- Основные: pydantic-settings и requests.
- `dev`: тесты, Ruff, ty, auto-typing-final.
- `data`: обработка таблиц и классические модели.
- `neural`: PyTorch.
- `research`: Jupyter, графики и Optuna, включает `data` и `neural`.
- `tracking`: MLflow.
- `orchestration`: Airflow для запуска DAG.
- `service`: FastAPI, Uvicorn, modern_di и зависимости классических моделей; PyTorch и MLflow не нужны.

Локально `just install` устанавливает все группы зависимостей.

## Доступные команды

| Команда | Назначение |
|---|---|
| `just api` | Запустить FastAPI на http://127.0.0.1:8001 |
| `just pipeline` | Поднять Airflow в Docker и выполнить скачивание, подготовку и обучение |
| `just mlflow-start` | Запустить MLflow в фоне на http://127.0.0.1:5001 |
| `just mlflow-stop` | Остановить процесс на порту MLflow |
| `just jupyter-start` | Запустить JupyterLab в фоне на http://127.0.0.1:5002 |
| `just jupyter-stop` | Остановить процесс на порту Jupyter |
| `just lint` | Форматирование и статические проверки |
| `just test` | Проверить подготовку, предсказание и API |

Justfile загружает `.env` в окружение; Python-классы не читают файл. `PipelineSettings` использует префикс `PIPELINE_`, `ExperimentSettings` — `EXPERIMENT_`, общие `MLflowSettings` — `MLFLOW_`. Например: `PIPELINE_SOURCE_URL`, `PIPELINE_TIMEOUT`, `EXPERIMENT_RANDOM_STATE`, `MLFLOW_PORT`. Перед повторным запуском MLflow или Jupyter остановите сервер соответствующей командой stop.

Параметры RandomForest задаются отдельными переменными в `.env`: например `RANDOM_FOREST_BASELINE__N_ESTIMATORS`, `RANDOM_FOREST_CLASS_PARAMETERS__MAX_DEPTH` и `RANDOM_FOREST_NSP_PARAMETERS__MAX_DEPTH`. Двойное подчёркивание отделяет группу от поля; `None` задаёт отсутствие ограничения. RandomForestSettings валидирует параметры.

## API

После установки зависимостей и подготовки моделей:

```bash
just api
```

Сервер работает в текущем терминале; Ctrl+C его останавливает. Порт и адрес задаются через API_HOST и API_PORT в .env. Swagger: http://127.0.0.1:8001/docs. Запуск API не запускает Airflow, обучение или MLflow.

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/demo/cases
curl -X POST http://127.0.0.1:8001/demo/records \
  -H 'Content-Type: application/json' -d '{"case_id":"D01"}'
curl http://127.0.0.1:8001/records
```

Ответ отправки содержит короткий record_id, предсказанные и истинные CLASS/NSP. GET /records/{record_id} возвращает также 21 исходный признак. Каждая отправка создаёт новую запись; данные сохраняются в runtime/service/analyses.db. Фиксированные примеры находятся в src/classifier/api/resources/demo_cases.csv.

POST /predict принимает объект features с 21 именованным признаком и возвращает предсказания без сохранения. CLASS и NSP во входе запрещены. GET /health проверяет процесс. Модели и CSV загружаются в lifespan при старте приложения. Ошибка загрузки останавливает запуск. Модели и демопримеры хранятся в AppCache. Соединение SQLite создаётся один раз на запрос и закрывается DI после его завершения.

Структура API повторяет netology-aiagnt: app.py, routes.py, models.py, ioc.py, settings.py и __main__.py. AppCache и PredictionsRepository имеют APP scope; соединение, AnalysisRepository и SubmitDemoRecordUseCase — REQUEST scope. HTML-интерфейс пока не реализован; API можно использовать через Swagger.

## Рабочая папка

Всё генерируемое находится в `runtime/`, вне Git:

- `data/raw/`: оригинальный ZIP и извлечённый CTG.xls;
- `data/prepared/`: очищенная таблица и train/validation/test;
- `models/`: сохранённые модели, параметры и зависимости;
- `service/`: SQLite исследований;
- `airflow/`: служебные файлы и логи Airflow;
- `reports/trained_classifier_comparison_metrics.csv`: итоговые метрики baseline и выбранных моделей;
- `mlflow/`: SQLite, `artifacts/` и `logs.log`;
Отчёты `.coverage`, `coverage.json` и кеш `pytest-cache/` создаются в корневой папке `tests/`, рядом с тестами, и исключены из Git.
- `jupyter/`: `logs.log`, профиль `ipython/` и служебные файлы Jupyter;

Исследование воспроизводится последовательным выполнением блокнотов 01–04 из `experiments/` после установки зависимостей и запуска MLflow.

Для воспроизведения подготовки и обучения выбранных классических моделей:

```bash
just pipeline
```

Нужен запущенный Docker. Команда собирает образ Airflow, запускает контейнер и последовательно выполняет три задачи DAG. После завершения контейнер удаляется, включая завершение с ошибкой; логи и результаты остаются в `runtime/`. Интерфейс Airflow доступен во время выполнения на http://127.0.0.1:5003, MLflow — на http://127.0.0.1:5001. Подробнее: [пайплайн](docs/pipeline-plan.md).

## План

[Сверка с заданием](docs/assignment-checklist.md) фиксирует выполненные требования и оставшуюся работу. [Пайплайн подготовки и обучения](docs/pipeline-plan.md) реализован через Airflow. Следующий этап — frontend для работающего API и автоматический демонстрационный поток. Исследования описаны в [experiments/README.md](experiments/README.md).

Источник: [UCI Cardiotocography](https://archive.ics.uci.edu/dataset/193/cardiotocography), Campos & Bernardes (2000), DOI 10.24432/C51S4N, CC BY 4.0.
