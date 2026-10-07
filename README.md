# CTG classifier demo

Сейчас реализованы только окружение, Justfile, MLflow/Jupyter и скрипт скачивания оригинального датасета. Подготовка, EDA, обучение и сервис отложены до совместного разбора.

## Запуск

Из корня проекта, без ручной активации окружения и переменных перед командами:

```bash
just lock
just install
just mlflow-start
just jupyter-start
```

Базовые команды скопированы из netology-aiagnt. `just lock` выполняет `uv lock --upgrade`; `just install` устанавливает все группы в отдельную `.venv`. Форматирование и проверки входят в `just lint`. Тесты — `just test`.

## Группы зависимостей

- Основные: pydantic-settings.
- `dev`: тесты, Ruff, ty, auto-typing-final.
- `data`: библиотеки будущей работы с таблицами.
- `research`: Jupyter и графики, включает `data`.
- `tracking`: MLflow.

Локально `just install` устанавливает все группы зависимостей.

## Доступные команды

| Команда | Назначение |
|---|---|
| `just fetch_dataset` | Скачать и сохранить оригинальный ZIP |
| `just mlflow-start` | Запустить MLflow в фоне на http://127.0.0.1:5001 |
| `just mlflow-stop` | Остановить процесс на порту MLflow |
| `just mlflow-logs` | Смотреть лог MLflow |
| `just jupyter-start` | Запустить JupyterLab в фоне на http://127.0.0.1:5002 |
| `just jupyter-stop` | Остановить процесс на порту Jupyter |
| `just lint` | Форматирование и статические проверки |
| `just test` | Проверить скачивание |

Команды запуска напрямую вызывают MLflow и Jupyter через uv. Настройки команд берутся из .env: `MLFLOW_PORT`, `JUPYTER_PORT`. Скрипт скачивания читает `DATA_SOURCE_URL`, `DATA_TIMEOUT` через pydantic-settings. Перед повторным запуском остановите сервер соответствующей командой stop.

## Рабочая папка

Всё генерируемое находится в `runtime/`, вне Git:

- `data/raw/`: оригинальный ZIP датасета;
- `mlflow/`: SQLite, `artifacts/` и `logs.log`;
Отчёты `.coverage`, `coverage.json` и кеш `pytest-cache/` создаются в корневой папке `tests/`, рядом с тестами, и исключены из Git.
- `jupyter/`: `logs.log`, профиль `ipython/` и служебные файлы Jupyter;

Существующий ZIP был скачан ранее с UCI. Новый downloader проверен локальными тестами; его сетевой запуск ещё не проверен. Никакой подготовки или разбиения команда скачивания не выполняет.

## План

[План и текущий статус](docs/project-plan.md), раздел 12. Следующие этапы не выполняются автоматически. Сначала совместный разбор исходных данных, затем согласование подготовки и разбиения.

Источник: [UCI Cardiotocography](https://archive.ics.uci.edu/dataset/193/cardiotocography), Campos & Bernardes (2000), DOI 10.24432/C51S4N, CC BY 4.0.
