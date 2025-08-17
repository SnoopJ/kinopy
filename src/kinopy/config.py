from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

from kinopy.provider import (
    SomervilleTheatreProvider,
)


class KinopyTomlSettingsSource(TomlConfigSettingsSource):
    def __init__(self, settings_cls: type[BaseSettings], toml_file="kinopy.toml"):
        self.toml_file_path = toml_file
        self.toml_data = self._read_files(self.toml_file_path).get("kinopy", {})

        self.toml_data.setdefault("provider", None)

        # NOTE:2025-08-17:This awful super() construction is unfortunately necessary, we need to call
        # InitSettingsSource.__init__() and NOT call TomlConfigSettingsSource.__init__()
        super(TomlConfigSettingsSource, self).__init__(settings_cls, self.toml_data)


# NOTE:2025-08-17:To add a configuration section for a new provider, import it and follow the example here.
# The provider settings sections should be Optional in general, a provider is meant to be discarded if it is not configured.
class KinopyProviderSettings(BaseSettings):
    somerville_theatre: Optional[SomervilleTheatreProvider.Config] = None


class KinopySettings(BaseSettings):
    model_config = SettingsConfigDict(toml_file="kinopy.toml")

    provider: Optional[KinopyProviderSettings]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (KinopyTomlSettingsSource(settings_cls),)


kinopy_config = KinopySettings()
