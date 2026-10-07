import typing
from unittest.mock import MagicMock

import pytest
import requests

from classifier.data.download import download_dataset
from classifier.data.settings import DataSettings


def test_download_saves_original_file(tmp_path, monkeypatch):
    monkeypatch.setattr("classifier.settings.PROJECT_ROOT", tmp_path)
    response: typing.Final = MagicMock()
    response.__enter__.return_value = response
    response.content = b"dataset archive"
    get: typing.Final = MagicMock(return_value=response)
    monkeypatch.setattr("classifier.data.download.requests.get", get)
    settings: typing.Final = DataSettings(_env_file=None)

    archive: typing.Final = download_dataset(settings)

    get.assert_called_once_with(settings.source_url, timeout=settings.timeout)
    response.raise_for_status.assert_called_once_with()
    assert archive == settings.raw_dir / "cardiotocography.zip"
    assert archive.read_bytes() == b"dataset archive"


def test_failed_download_preserves_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr("classifier.settings.PROJECT_ROOT", tmp_path)
    response: typing.Final = MagicMock()
    response.__enter__.return_value = response
    response.raise_for_status.side_effect = requests.HTTPError
    monkeypatch.setattr("classifier.data.download.requests.get", MagicMock(return_value=response))
    settings: typing.Final = DataSettings(_env_file=None)
    settings.raw_dir.mkdir(parents=True)
    archive: typing.Final = settings.raw_dir / "cardiotocography.zip"
    archive.write_bytes(b"previous download")

    with pytest.raises(requests.HTTPError):
        download_dataset(settings)

    assert archive.read_bytes() == b"previous download"
