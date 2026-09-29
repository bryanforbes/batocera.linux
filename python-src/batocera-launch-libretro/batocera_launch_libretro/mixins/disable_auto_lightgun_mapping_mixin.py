from __future__ import annotations

from batocera_common.dataclasses import cached_dataclass, cached_property

from ..core import Core


@cached_dataclass
class DisableAutoLightgunMappingMixin(Core):
    @cached_property
    def map_lightguns(self) -> bool:
        return self.config.get_bool('lightgun_map', False)
