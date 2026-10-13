import logging
import typing
from pathlib import Path

import requests

from classifier.pipeline.settings import PipelineSettings

LOGGER_OBJ: typing.Final = logging.getLogger(__name__)


def download_dataset() -> Path:
    pipeline_settings: typing.Final = PipelineSettings()
    pipeline_settings.raw_dir.mkdir(parents=True, exist_ok=True)
    archive: typing.Final = Path(pipeline_settings.raw_dir, "cardiotocography.zip")
    with requests.get(pipeline_settings.source_url, timeout=pipeline_settings.timeout) as response:
        response.raise_for_status()
        content: typing.Final = response.content
    archive.write_bytes(content)
    LOGGER_OBJ.info("Downloaded dataset: %s", archive)
    return archive
