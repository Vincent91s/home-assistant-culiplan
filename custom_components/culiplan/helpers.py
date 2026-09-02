"""Shared helpers for the Culiplan integration."""

from __future__ import annotations

from datetime import UTC, date, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN, MANIFEST_VERSION


def _build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return a canonical DeviceInfo for all Culiplan entities.

    ``sw_version`` comes from ``const.MANIFEST_VERSION``, which is read once at
    module import. This used to read manifest.json on every call — but the
    function runs inside platform setup on the event loop, so HA flagged it as
    a blocking call on every startup.
    """
    sw_version: str | None = None if MANIFEST_VERSION == "dev" else MANIFEST_VERSION

    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Culiplan",
        manufacturer="Culiplan",
        model="Meal Planner",
        sw_version=sw_version,
        configuration_url="https://culiplan.com",
        entry_type=DeviceEntryType.SERVICE,
    )


def parse_dt(value: str) -> datetime:
    """Parse an ISO 8601 date or datetime string into a timezone-aware datetime."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return datetime.combine(
            date.fromisoformat(value), datetime.min.time(), tzinfo=UTC
        )
