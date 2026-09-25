"""Bambu AMS Spool Sync sensors."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.device_registry import (
    async_get as async_get_device_registry,
)
from homeassistant.helpers.entity_registry import (
    async_get as async_get_entity_registry,
)

from .const import (
    CONF_SPOOLMAN_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


# ============================================================
# BAMBU FILAMENT PROFILES
# ============================================================

BAMBU_PROFILES = {
    "PLA": {
        "filament_id": "GFL99",
        "tray_type": "PLA",
        "nozzle_temp_min": 190,
        "nozzle_temp_max": 240,
    },
    "PETG": {
        "filament_id": "GFG99",
        "tray_type": "PETG",
        "nozzle_temp_min": 220,
        "nozzle_temp_max": 270,
    },
    "ABS": {
        "filament_id": "GFB99",
        "tray_type": "ABS",
        "nozzle_temp_min": 240,
        "nozzle_temp_max": 280,
    },
    "TPU": {
        "filament_id": "GFU98",
        "tray_type": "TPU",
        "nozzle_temp_min": 220,
        "nozzle_temp_max": 250,
    },
    "PLA-CF": {"filament_id": "GFL98", "tray_type": "PLA-CF", "nozzle_temp_min": 210, "nozzle_temp_max": 240},
    "PLA-HIGH-SPEED": {"filament_id": "GFL95", "tray_type": "PLA", "nozzle_temp_min": 190, "nozzle_temp_max": 240},
    "PLA-SILK": {"filament_id": "GFL96", "tray_type": "PLA", "nozzle_temp_min": 190, "nozzle_temp_max": 240},
    "PETG-HF": {"filament_id": "GFG96", "tray_type": "PETG", "nozzle_temp_min": 230, "nozzle_temp_max": 260},
    "PCTG": {"filament_id": "GFG97", "tray_type": "PCTG", "nozzle_temp_min": 230, "nozzle_temp_max": 260},
    "PETG-CF": {"filament_id": "GFG98", "tray_type": "PETG-CF", "nozzle_temp_min": 240, "nozzle_temp_max": 280},
    "ASA": {"filament_id": "GFB98", "tray_type": "ASA", "nozzle_temp_min": 240, "nozzle_temp_max": 280},
    "PC": {"filament_id": "GFC99", "tray_type": "PC", "nozzle_temp_min": 250, "nozzle_temp_max": 300},
    "PA": {"filament_id": "GFN99", "tray_type": "PA", "nozzle_temp_min": 240, "nozzle_temp_max": 280},
    "PA-CF": {"filament_id": "GFN98", "tray_type": "PA-CF", "nozzle_temp_min": 250, "nozzle_temp_max": 290},
    "PPA-CF": {"filament_id": "GFN97", "tray_type": "PPA-CF", "nozzle_temp_min": 280, "nozzle_temp_max": 300},
    "PPA-GF": {"filament_id": "GFN96", "tray_type": "PPA-GF", "nozzle_temp_min": 280, "nozzle_temp_max": 300},
    "PP": {"filament_id": "GFP97", "tray_type": "PP", "nozzle_temp_min": 220, "nozzle_temp_max": 250},
    "PP-CF": {"filament_id": "GFP96", "tray_type": "PP-CF", "nozzle_temp_min": 230, "nozzle_temp_max": 260},
    "PP-GF": {"filament_id": "GFP95", "tray_type": "PP-GF", "nozzle_temp_min": 230, "nozzle_temp_max": 260},
    "PE": {"filament_id": "GFP99", "tray_type": "PE", "nozzle_temp_min": 220, "nozzle_temp_max": 250},
    "PE-CF": {"filament_id": "GFP98", "tray_type": "PE-CF", "nozzle_temp_min": 230, "nozzle_temp_max": 260},
    "PHA": {"filament_id": "GFR98", "tray_type": "PHA", "nozzle_temp_min": 190, "nozzle_temp_max": 230},
    "EVA": {"filament_id": "GFR99", "tray_type": "EVA", "nozzle_temp_min": 190, "nozzle_temp_max": 230},
    "PVA": {"filament_id": "GFS99", "tray_type": "PVA", "nozzle_temp_min": 190, "nozzle_temp_max": 220},
    "BVOH": {"filament_id": "GFS97", "tray_type": "BVOH", "nozzle_temp_min": 190, "nozzle_temp_max": 220},
    "HIPS": {"filament_id": "GFS98", "tray_type": "HIPS", "nozzle_temp_min": 220, "nozzle_temp_max": 260},
}


# ============================================================
# SETUP
# ============================================================

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Discover Bambu AMS trays."""

    entity_registry = async_get_entity_registry(hass)
    device_registry = async_get_device_registry(hass)

    entities = []

    for entity in entity_registry.entities.values():

        if entity.platform != "bambu_lab":
            continue

        entity_id = entity.entity_id

        if "_ams_" not in entity_id or "_tray_" not in entity_id:
            continue

        device = None

        if entity.device_id:
            device = device_registry.async_get(entity.device_id)

        ams_index = BambuAMSTraySensor._get_ams_index(device)
        tray_index = BambuAMSTraySensor._get_tray_number_from_entity_id(
            entity_id
        )

        if ams_index is None or tray_index is None:
            _LOGGER.warning(
                "Skipping Bambu tray %s: unable to determine its AMS/tray indices",
                entity_id,
            )
            continue

        entities.append(
            BambuAMSTraySensor(
                hass=hass,
                entry=entry,
                entity_id=entity_id,
                device=device,
                ams_index=ams_index,
                tray_index=tray_index,
            )
        )

    _LOGGER.info(
        "Bambu AMS Spool Sync discovered %d AMS tray entities",
        len(entities),
    )

    async_add_entities(entities)

    async def _handle_assignment_state_change(event: Event) -> None:
        """Handle Spoolman assignment changes for one AMS tray."""
        # Spoolman may publish one initial state event per assigned spool while
        # HA is starting. Ignore those to avoid a startup fan-out across trays.
        if not hass.is_running:
            return

        entity_id = event.data.get("entity_id")
        if not entity_id:
            return
        registry_entry = entity_registry.async_get(entity_id)
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if registry_entry is None or new_state is None:
            return

        runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        if (
            registry_entry.platform != "spoolman"
            or not registry_entry.unique_id.endswith("_extra_active_tray")
        ):
            return

        old_value = str(old_state.state).strip().strip('"') if old_state else ""
        tray_id = str(new_state.state).strip().strip('"')
        spool_id = new_state.attributes.get("spool_id")
        if spool_id is None and old_state is not None:
            spool_id = old_state.attributes.get("spool_id")
        if spool_id is None:
            match = re.search(r"_spool_(\d+)_extra_active_tray$", registry_entry.unique_id)
            if match:
                spool_id = match.group(1)
        try:
            spool_id = int(spool_id)
        except (TypeError, ValueError):
            _LOGGER.warning("Cannot identify Spoolman spool for assignment sensor %s", entity_id)
            return

        if not tray_id:
            return
        if tray_id == old_value:
            return

        target = _find_bambu_tray(hass, entry, tray_id, entity_registry, device_registry)
        if target is None:
            _LOGGER.warning("No Bambu AMS tray matches Spoolman assignment %s", tray_id)
            return
        target = runtime.setdefault("targets", {}).setdefault(
            target._bambu_entity_id, target
        )

        await target._async_process_assignment(tray_id, spool_id)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "unsub": hass.bus.async_listen(
            "state_changed", _handle_assignment_state_change
        ),
        "targets": {entity._bambu_entity_id: entity for entity in entities},
    }

    # Assignment events synchronize only the newly assigned Spoolman tray.
    # Bambu's reported empty state does not block sending the assigned profile.


def _find_bambu_tray(
    hass: HomeAssistant,
    entry: ConfigEntry,
    spoolman_tray_id: str,
    entity_registry,
    device_registry,
) -> BambuAMSTraySensor | None:
    """Resolve an assignment to the corresponding currently registered Bambu tray."""
    for registry_entry in entity_registry.entities.values():
        if registry_entry.platform != "bambu_lab":
            continue
        entity_id = registry_entry.entity_id
        if not entity_id.startswith("sensor.") or "_ams_" not in entity_id or "_tray_" not in entity_id:
            continue
        device = device_registry.async_get(registry_entry.device_id) if registry_entry.device_id else None
        ams_index = BambuAMSTraySensor._get_ams_index(device)
        tray_index = BambuAMSTraySensor._get_tray_number_from_entity_id(entity_id)
        if ams_index is None or tray_index is None:
            continue
        candidate = BambuAMSTraySensor(hass, entry, entity_id, device, ams_index, tray_index)
        expected_suffix = candidate._get_spoolman_tray_id()
        if expected_suffix and spoolman_tray_id.casefold().endswith(expected_suffix.casefold()):
            return candidate
    return None


# ============================================================
# AMS SENSOR
# ============================================================

class BambuAMSTraySensor(SensorEntity):
    """Represent a Bambu AMS tray."""

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        entity_id: str,
        device,
        ams_index: int,
        tray_index: int,
    ) -> None:
        """Initialize the AMS tray sensor."""

        self.hass = hass
        self.entry = entry

        self._bambu_entity_id = entity_id
        self._device = device
        self._ams_index = ams_index
        self._tray_index = tray_index

        self._spool = None
        self._spoolman_tray = None

        # Prevent sending the exact same filament repeatedly.
        self._last_set_filament = None

        self._attr_unique_id = f"{DOMAIN}_{entity_id}"

        tray_number = self._get_tray_number()

        printer_name = None
        ams_name = None

        if device:
            ams_name = getattr(device, "name", None)

        if ams_name and "_AMS_" in ams_name:
            printer_name = ams_name.split(
                "_AMS_",
                1,
            )[0]

        if printer_name and tray_number:
            self._attr_name = (
                f"{printer_name} AMS 1 Tray {tray_number}"
            )
        elif tray_number:
            self._attr_name = f"AMS Tray {tray_number}"
        else:
            self._attr_name = entity_id

        self._attr_native_value = "unassigned"

        if device:
            self._attr_device_info = {
                "identifiers": {
                    (
                        DOMAIN,
                        device.id,
                    )
                },
                "name": device.name,
            }

    # ========================================================
    # UPDATE
    # ========================================================

    async def async_added_to_hass(self) -> None:
        """Set up the entity; assignments are handled by the platform listener."""
        await super().async_added_to_hass()

    async def _async_process_assignment(
        self,
        tray_id: str,
        spool_id: int,
    ) -> None:
        """Fetch and synchronize the one spool newly assigned to this tray."""

        spoolman_url = self.entry.data.get(
            CONF_SPOOLMAN_URL
        )

        if not spoolman_url:
            _LOGGER.error(
                "No Spoolman URL configured"
            )
            return

        try:

            self._spoolman_tray = tray_id

            self._spool = await self.hass.async_add_executor_job(
                self._get_spool,
                spoolman_url,
                spool_id,
            )

            # Ignore stale/incorrect state events if the spool no longer owns
            # this tray by the time its Spoolman record is fetched.
            current_assignment = str(
                (self._spool or {}).get("extra", {}).get("active_tray", "")
            ).strip().strip('"')
            if not self._spool or current_assignment != tray_id:
                self._spool = None
                self._attr_native_value = "unassigned"
                if self.entity_id:
                    self.async_write_ha_state()
                return

            if self._spool:

                filament = (
                    self._spool.get("filament")
                    or {}
                )

                self._attr_native_value = filament.get(
                    "name",
                    "assigned",
                )

                _LOGGER.info(
                    "AMS tray %s -> Spoolman tray %s -> spool %s",
                    self._bambu_entity_id,
                    tray_id,
                    self._spool.get("id"),
                )

                # The Spoolman assignment is the desired tray configuration.
                # Send it even when Bambu reports the physical slot as empty;
                # some AMS slots do not report insertion reliably until later.
                await self._async_set_bambu_filament()

            else:

                self._attr_native_value = "unassigned"

                _LOGGER.debug(
                    "No Spoolman spool assigned to %s",
                    tray_id,
                )

        except Exception as err:

            _LOGGER.error(
                "Unable to update Spoolman for %s: %s",
                self._bambu_entity_id,
                err,
            )

        if self.entity_id:
            self.async_write_ha_state()

    # ========================================================
    # SET BAMBU FILAMENT
    # ========================================================

    def _is_bambu_lab_filament(self, filament: dict[str, Any]) -> bool:
        """Return whether the spool is a Bambu Lab branded filament."""
        vendor = filament.get("vendor") or {}
        vendor_name = vendor.get("name", "") if isinstance(vendor, dict) else str(vendor)
        return re.sub(r"[^a-z0-9]", "", str(vendor_name).casefold()) == "bambulab"

    async def _async_set_bambu_filament(self) -> None:
        """Set the assigned Spoolman filament on the Bambu AMS."""

        if not self._spool:
            return

        tray_id = self._get_bambu_tray_id()

        if not tray_id:
            _LOGGER.warning(
                "Unable to determine Bambu tray ID for %s",
                self._bambu_entity_id,
            )
            return

        filament = (
            self._spool.get("filament")
            or {}
        )

        filament = self._spool.get("filament") or {}
        if self._is_bambu_lab_filament(filament):
            _LOGGER.info(
                "Skipping Bambu Lab RFID filament on %s (spool %s)",
                self._bambu_entity_id,
                self._spool.get("id"),
            )
            return

        material = str(
            filament.get("material")
            or ""
        ).upper()

        profile_key = material.replace("_", "-").replace(" ", "-")

        if profile_key not in BAMBU_PROFILES:

            if profile_key.startswith("PLA"):
                profile_key = "PLA-CF" if "CF" in profile_key else "PLA"
            elif profile_key.startswith("PETG"):
                profile_key = "PETG-CF" if "CF" in profile_key else "PETG-HF" if "HF" in profile_key else "PETG"
            elif profile_key.startswith("ABS"):
                profile_key = "ABS"
            elif profile_key.startswith("TPU"):
                profile_key = "TPU"
            elif profile_key.startswith("PA"):
                profile_key = "PPA-CF" if "PPA" in profile_key and "CF" in profile_key else "PPA-GF" if "PPA" in profile_key and "GF" in profile_key else "PA-CF" if "CF" in profile_key else "PA"
            elif profile_key == "ASA-CF":
                profile_key = "ASA"

        profile = BAMBU_PROFILES.get(
            profile_key
        )

        if not profile:

            _LOGGER.warning(
                "Unable to determine Bambu filament profile "
                "for %s: material=%s",
                self._bambu_entity_id,
                material,
            )

            return

        profile = dict(profile)
        for temp_key in ("nozzle_temp_min", "nozzle_temp_max"):
            try:
                profile[temp_key] = int(filament.get(temp_key, profile[temp_key]))
            except (TypeError, ValueError):
                pass

        # ----------------------------------------------------
        # COLOR
        #
        # Bambu expects RGBA:
        #
        # RRGGBBAA
        #
        # Spoolman normally gives RRGGBB.
        # Add FF for full opacity.
        # ----------------------------------------------------

        color = (
            filament.get("color_hex")
            or filament.get("color")
            or "FFFFFF"
        )

        color = str(
            color
        ).replace(
            "#",
            "",
        ).upper()

        if len(color) == 6:
            color += "FF"

        if len(color) != 8:

            _LOGGER.warning(
                "Invalid filament color %s for spool %s",
                color,
                self._spool.get("id"),
            )

            return

        # ----------------------------------------------------
        # BUILD UNIQUE COMMAND SIGNATURE
        # ----------------------------------------------------

        command_signature = (
            tray_id,
            profile["filament_id"],
            profile["tray_type"],
            color,
            profile["nozzle_temp_min"],
            profile["nozzle_temp_max"],
        )

        if self._bambu_filament_matches(
            profile,
            color,
        ):
            _LOGGER.debug(
                "Bambu filament already matches Spoolman for %s",
                self._bambu_entity_id,
            )
            return

        # Don't repeatedly send the same command.
        if (
            self._last_set_filament
            == command_signature
        ):

            _LOGGER.debug(
                "Bambu filament already set for %s",
                self._bambu_entity_id,
            )

            return

        _LOGGER.info(
            "Setting Bambu filament for %s: "
            "tray=%s id=%s type=%s color=%s",
            self._bambu_entity_id,
            tray_id,
            profile["filament_id"],
            profile["tray_type"],
            color,
        )

        try:

            await self.hass.services.async_call(
                "bambu_lab",
                "set_filament",
                {
                    "entity_id": self._bambu_entity_id,
                    "tray_info_idx": profile[
                        "filament_id"
                    ],
                    "tray_color": color,
                    "tray_type": profile[
                        "tray_type"
                    ],
                    "nozzle_temp_min": profile[
                        "nozzle_temp_min"
                    ],
                    "nozzle_temp_max": profile[
                        "nozzle_temp_max"
                    ],
                },
                blocking=True,

            )

            self._last_set_filament = (
                command_signature
            )

            _LOGGER.info(
                "Bambu set_filament completed for %s",
                self._bambu_entity_id,
            )

        except Exception as err:

            _LOGGER.error(
                "Failed to set Bambu filament for %s: %s",
                self._bambu_entity_id,
                err,
            )

    # ========================================================
    # BAMBU TRAY ID
    # ========================================================

    def _get_bambu_tray_id(self) -> str | None:
        """Return the Bambu tray identifier used by set_filament."""

        if not self._device:
            return None

        bambu_identifier = self._get_bambu_identifier(
            self._device
        )

        if not bambu_identifier:
            return None

        tray_number = self._get_tray_number()

        if not tray_number:
            return None

        return (
            f"{bambu_identifier}_tray_{tray_number}"
        )

    # ========================================================
    # SPOOLMAN
    # ========================================================

    def _get_spool(
        self,
        spoolman_url: str,
        spool_id: int,
    ) -> dict[str, Any] | None:
        """Read only the assigned spool record from Spoolman."""

        url = f"{spoolman_url.rstrip('/')}/api/v1/spool/{spool_id}"

        request = urllib.request.Request(
            url
        )

        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:

            data = json.loads(
                response.read().decode()
            )

        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return next((item for item in data["items"] if item.get("id") == spool_id), None)
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            return data["data"]
        return data if isinstance(data, dict) else None

    # ========================================================
    # BAMBU IDENTIFIER
    # ========================================================

    @staticmethod
    def _get_bambu_identifier(
        device,
    ) -> str | None:
        """Return the Bambu identifier for a HA device."""

        if not device:
            return None

        for identifier in device.identifiers:

            if (
                isinstance(
                    identifier,
                    tuple,
                )
                and len(identifier) >= 2
                and identifier[0]
                == "bambu_lab"
            ):

                return str(
                    identifier[1]
                )

        return None

    # ========================================================
    # PARENT PRINTER
    # ========================================================

    @staticmethod
    def _get_parent_bambu_device(
        device_registry,
        device,
    ):
        """Find the parent Bambu printer for an AMS device."""

        if not device:
            return None

        via_device_id = getattr(
            device,
            "via_device_id",
            None,
        )

        if via_device_id:

            parent = device_registry.async_get(
                via_device_id
            )

            if parent:

                identifier = (
                    BambuAMSTraySensor._get_bambu_identifier(
                        parent
                    )
                )

                if identifier:
                    return parent

        name = getattr(
            device,
            "name",
            "",
        ) or ""

        if "_AMS_" in name:

            printer_name = name.split(
                "_AMS_",
                1,
            )[0]

            for candidate in (
                device_registry.devices.values()
            ):

                candidate_name = getattr(
                    candidate,
                    "name",
                    "",
                ) or ""

                if (
                    candidate_name
                    == printer_name
                ):

                    identifier = (
                        BambuAMSTraySensor._get_bambu_identifier(
                            candidate
                        )
                    )

                    if identifier:
                        return candidate

        return None

    @staticmethod
    def _get_printer_device(device_registry, device):
        """Return a Bambu printer device, resolving an AMS device to its parent."""
        if not device:
            return None
        if BambuAMSTraySensor._get_bambu_identifier(device):
            return device
        return BambuAMSTraySensor._get_parent_bambu_device(
            device_registry, device
        )

    # ========================================================
    # TRAY NUMBER
    # ========================================================

    def _get_tray_number(
        self,
    ) -> str | None:
        """Extract AMS tray number from entity ID."""

        entity = self._bambu_entity_id

        marker = "_tray_"

        if marker not in entity:
            return None

        tray = entity.split(
            marker,
            1,
        )[1]

        if not tray.isdigit():
            return None

        return tray

    @staticmethod
    def _get_tray_number_from_entity_id(entity_id: str) -> int | None:
        """Return the zero-based tray index from a Bambu tray entity ID."""
        match = re.search(r"_tray_([1-4])$", entity_id)
        if not match:
            return None
        return int(match.group(1)) - 1

    @staticmethod
    def _get_ams_index(device) -> int | None:
        """Map the Bambu AMS device name to its active_tray AMS index."""
        if not device:
            return None

        match = re.search(r"_AMS_(\d+)$", getattr(device, "name", "") or "")
        if not match:
            return None

        device_ams_number = int(match.group(1))
        # Bambu Lab names standard AMS units from 1 while the model uses 0-based
        # indices. AMS HT indices are already in the 128+ range.
        return (
            device_ams_number
            if device_ams_number >= 128
            else device_ams_number - 1
        )

    def _bambu_filament_matches(
        self,
        profile: dict[str, Any],
        color: str,
    ) -> bool:
        """Compare the current Bambu tray attributes with the target profile."""
        state = self.hass.states.get(self._bambu_entity_id)
        if state is None:
            return False

        attributes = state.attributes

        def normalized_color(value) -> str:
            value = str(value or "").replace("#", "").upper()
            if len(value) == 6:
                value += "FF"
            return value

        def normalized_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return (
            str(attributes.get("filament_id") or "").upper()
            == profile["filament_id"].upper()
            and str(attributes.get("type") or "").upper()
            == profile["tray_type"].upper()
            and normalized_color(attributes.get("color")) == color
            and normalized_int(attributes.get("nozzle_temp_min"))
            == profile["nozzle_temp_min"]
            and normalized_int(attributes.get("nozzle_temp_max"))
            == profile["nozzle_temp_max"]
        )

    # ========================================================
    # SPOOLMAN TRAY ID
    # ========================================================

    def _get_spoolman_tray_id(
        self,
    ) -> str | None:
        """Build dynamic Spoolman tray identifier."""

        if not self._device:

            _LOGGER.warning(
                "No HA device found for %s",
                self._bambu_entity_id,
            )

            return None

        device_registry = (
            async_get_device_registry(
                self.hass
            )
        )

        ams_identifier = (
            self._get_bambu_identifier(
                self._device
            )
        )

        if not ams_identifier:

            _LOGGER.warning(
                "No Bambu identifier found for AMS device %s",
                self._device.name,
            )

            return None

        printer = (
            self._get_parent_bambu_device(
                device_registry,
                self._device,
            )
        )

        if not printer:

            _LOGGER.warning(
                "Unable to find parent Bambu printer for AMS %s",
                self._device.name,
            )

            return None

        printer_identifier = (
            self._get_bambu_identifier(
                printer
            )
        )

        if not printer_identifier:

            _LOGGER.warning(
                "No Bambu identifier found for printer %s",
                printer.name,
            )

            return None

        tray_number = (
            self._get_tray_number()
        )

        if not tray_number:

            _LOGGER.warning(
                "Unable to determine tray number from %s",
                self._bambu_entity_id,
            )

            return None

        tray_id = (
            f"{printer_identifier}_AMS_{ams_identifier}"
            f"_tray_{tray_number}"
        )

        _LOGGER.debug(
            "Dynamic Bambu -> Spoolman mapping: %s -> %s",
            self._bambu_entity_id,
            tray_id,
        )

        return tray_id

    # ========================================================
    # ATTRIBUTES
    # ========================================================

    @property
    def extra_state_attributes(
        self,
    ):
        """Return AMS tray and Spoolman information."""

        attributes = {
            "bambu_entity_id": (
                self._bambu_entity_id
            ),
            "spoolman_tray": (
                self._spoolman_tray
            ),
        }

        if self._spool:

            filament = (
                self._spool.get("filament")
                or {}
            )

            attributes.update(
                {
                    "spool_id": (
                        self._spool.get("id")
                    ),
                    "filament": (
                        filament.get("name")
                    ),
                    "material": (
                        filament.get("material")
                    ),
                    "vendor": (
                        filament.get("vendor")
                        or {}
                    ).get(
                        "name"
                    ),
                    "color": (
                        filament.get(
                            "color_hex"
                        )
                        or filament.get(
                            "color"
                        )
                    ),
                }
            )

        return attributes
