"""Ecovacs util functions."""

from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING

from deebot_client.capabilities import Capabilities

from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from .entity import (
    EcovacsCapabilityEntityDescription,
    EcovacsDescriptionEntity,
    EcovacsEntity,
)

if TYPE_CHECKING:
    from .controller import EcovacsController


def get_client_device_id(hass: HomeAssistant, self_hosted: bool) -> str:
    """Get client device id."""
    if self_hosted:
        return f"HA-{slugify(hass.config.location_name)}"

    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(8)
    )


def get_supported_entitites(
    controller: EcovacsController,
    entity_class: type[EcovacsDescriptionEntity],
    descriptions: tuple[EcovacsCapabilityEntityDescription, ...],
) -> list[EcovacsEntity]:
    """Return all supported entities for all devices."""
    return [
        entity_class(device, capability, description)
        for device in controller.devices(Capabilities)
        for description in descriptions
        if isinstance(device.capabilities, description.device_capabilities)
        if (capability := description.capability_fn(device.capabilities))
    ]
