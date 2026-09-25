# Bambu AMS Spool Sync

Home Assistant custom integration that connects your spool inventory to your printer. When you assign a spool to an AMS tray in Spoolman Sync, this integration reads the assignment and sends the matching filament profile and color to the corresponding Bambu AMS tray.

## Required software

All of the following components are needed. Spoolman and Spoolman Sync must be running services reachable on your network; Docker containers and Home Assistant add-ons are common ways to run them.

> Installing the Home Assistant integrations alone is not enough: the **Spoolman server** and **Spoolman Sync application** must also be running. If Home Assistant runs in a separate Docker container, make sure the Spoolman URL uses a host or network address Home Assistant can reach; `localhost` inside a container usually refers to that container itself.

| Icon | Component | What it does |
| --- | --- | --- |
| 🧵 | [Spoolman](https://github.com/Donkie/Spoolman) | The filament inventory and database. It stores each spool's material, color, and other filament details. Keep the Spoolman service running. |
| 🏷️ | [Spoolman Home Assistant integration](https://github.com/Disane87/spoolman-homeassistant) | Connects Home Assistant to Spoolman and exposes spool fields, including the `active_tray` extra field, as Home Assistant entities. This integration listens for changes to those assignment entities. |
| 🗂️ | [Spoolman Sync](https://github.com/gibz104/SpoolmanSync) | The interface used to assign a spool to a printer's AMS tray. It writes the assignment to Spoolman's `active_tray` field. Keep Spoolman Sync running wherever you host it, such as in a Docker container or add-on. |
| 🖨️ | [Bambu Lab Home Assistant integration](https://github.com/greghesp/ha-bambulab) | Connects Home Assistant to your Bambu printer, discovers its AMS tray entities, and provides the `bambu_lab.set_filament` action used to update a tray. |
| 🏠 | [Home Assistant](https://www.home-assistant.io/) | Runs this integration plus the Bambu Lab and Spoolman integrations. Home Assistant must be able to reach the Spoolman service and printer integration. |

**Spoolman Sync and the Bambu Lab integration have different roles:** Spoolman Sync records which spool is assigned to a tray; the Bambu Lab integration provides the actual printer and AMS tray entities. Bambu AMS Spool Sync connects those two sides.

### How the update flows

1. Assign a spool to an AMS tray in Spoolman Sync.
2. Spoolman Sync stores the assignment in Spoolman's `active_tray` extra field.
3. The Spoolman Home Assistant integration exposes the changed assignment as an entity state update.
4. Bambu AMS Spool Sync identifies the mapped Bambu tray, reads that spool's filament data from Spoolman, and compares it with the tray's current configuration.
5. If the configurations differ, it calls `bambu_lab.set_filament` for that tray only. Bambu Lab branded filament is skipped because the AMS can identify it using RFID.

An assignment change triggers the update even if Bambu Lab reports the tray as empty. Bambu's integration does not reliably expose physical filament insertion for every tray. Editing a spool's filament details without changing its tray assignment does not currently trigger a sync. This integration does not open its own MQTT connection.

This integration uses the Spoolman URL configured during setup. It does not ask for or use a Spoolman API key.

## Install with HACS

Add this repository to HACS as a custom repository:

1. In HACS, open **Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/demonkazuya/bambu-ams-spool-sync` and select **Integration** as the category.
4. Find **Bambu AMS Spool Sync**, install it, and restart Home Assistant.
5. Add the integration from **Settings → Devices & services → Add integration** and enter the base URL of your Spoolman service. Home Assistant must be able to reach that URL.

## Issues

Report problems or request features in the [GitHub issue tracker](https://github.com/demonkazuya/bambu-ams-spool-sync/issues).
