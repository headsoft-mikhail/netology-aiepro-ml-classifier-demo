import logging
import typing
from pathlib import Path

import requests

from classifier.data.settings import DataSettings

LOGGER_OBJ: typing.Final = logging.getLogger(__name__)


def download_dataset(settings: DataSettings) -> Path:
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    archive: typing.Final = settings.raw_dir / "cardiotocography.zip"
    with requests.get(settings.source_url, timeout=settings.timeout) as response:
        response.raise_for_status()
        content: typing.Final = response.content
    archive.write_bytes(content)
    LOGGER_OBJ.info("Downloaded dataset: %s", archive)
    return archive


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    download_dataset(DataSettings())
