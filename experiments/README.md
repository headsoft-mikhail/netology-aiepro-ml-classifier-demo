# Исследования

- [01_eda.ipynb](01_eda.ipynb): загрузка Raw Data, словарь колонок, очистка, сводные отчёты и выводы первичного EDA. Последняя ячейка сохраняет таблицу в `runtime/data/prepared/ctg_cleaned.csv`.
- [02_preparation.ipynb](02_preparation.ipynb): групповое разбиение 60/20/20, связь CLASS/NSP, исследование train, duration и выбор входных признаков. Сохраняет три подготовленные выборки.
- [03_classical_models.ipynb](03_classical_models.ipynb): начальное сравнение, RandomForest baseline, два этапа Optuna, итоговая оценка и сохранение классических моделей.
- [04_neural_models.ipynb](04_neural_models.ipynb): обучение MLP, подбор параметров, сравнение с классическими моделями на test, выбор моделей для сервиса и сохранение нейросетей.

В `ctg_cleaned.csv` сохраняются все колонки после очистки. В train/validation/test сохраняются 21 входной признак и две цели. Идентификаторы удаляются после группового разбиения; индикаторы паттернов исключаются. CLASS и NSP не подаются на вход модели.

Все четыре этапа исследования выполнены. Для сервиса выбраны оптимизированные RandomForest для обеих целей; MLP остаётся альтернативой. Подготовка и обучение RandomForest перенесены в [Airflow-пайплайн](../src/classifier/pipeline/dag.py). FastAPI и frontend реализованы; оставшиеся требования сдачи перечислены в [актуальной сверке](../docs/submission-gaps.md).


При пакетном повторном выполнении отключаем запись времени ячеек и состояния виджетов:

```bash
just --command uv run --group research --group tracking jupyter nbconvert \
  --execute --inplace --ExecutePreprocessor.timeout=1800 \
  --ExecutePreprocessor.record_timing=False --ExecutePreprocessor.store_widget_state=False \
  experiments/01_eda.ipynb experiments/02_preparation.ipynb \
  experiments/03_classical_models.ipynb experiments/04_neural_models.ipynb
```

В репозитории сохраняются код, пояснения, таблицы и графики. Служебные временные отметки и состояния индикаторов прогресса не сохраняются. Интерактивный запуск в Jupyter может создать их снова; перед коммитом их нужно убрать.
