from pathlib import Path

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from classifier.settings import PROJECT_ROOT, WorkspaceSettings


class DataSettings(WorkspaceSettings):
    model_config = SettingsConfigDict(
        env_prefix="DATA_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
        populate_by_name=True,
    )
    source_url: str = "https://archive.ics.uci.edu/static/public/193/cardiotocography.zip"
    timeout: float = Field(default=60, gt=0)

    @property
    def raw_dir(self) -> Path:
        return self.workspace / "data/raw"
