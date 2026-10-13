import typing
from unittest.mock import MagicMock

import pytest
import requests

from classifier.pipeline.download import download_dataset
from classifier.pipeline.settings import PipelineSettings


def test_download_saves_original_file(monkeypatch):
    response: typing.Final = MagicMock()
    response.__enter__.return_value = response
    response.content = b"dataset archive"
    get: typing.Final = MagicMock(return_value=response)
    monkeypatch.setattr("classifier.pipeline.download.requests.get", get)
    pipeline_settings: typing.Final = PipelineSettings()

    archive: typing.Final = download_dataset()

    get.assert_called_once_with(pipeline_settings.source_url, timeout=pipeline_settings.timeout)
    response.raise_for_status.assert_called_once_with()
    assert archive == pipeline_settings.raw_dir / "cardiotocography.zip"
    assert archive.read_bytes() == b"dataset archive"


def test_failed_download_preserves_existing_file(monkeypatch):
    response: typing.Final = MagicMock()
    response.__enter__.return_value = response
    response.raise_for_status.side_effect = requests.HTTPError
    monkeypatch.setattr("classifier.pipeline.download.requests.get", MagicMock(return_value=response))
    pipeline_settings: typing.Final = PipelineSettings()
    pipeline_settings.raw_dir.mkdir(parents=True)
    archive: typing.Final = pipeline_settings.raw_dir / "cardiotocography.zip"
    archive.write_bytes(b"previous download")

    with pytest.raises(requests.HTTPError):
        download_dataset()

    assert archive.read_bytes() == b"previous download"
