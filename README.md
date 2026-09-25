# Bambu AMS Spool Sync

Home Assistant custom integration that applies the filament configuration of a spool assigned in Spoolman Sync to its mapped Bambu AMS tray.

## What it does

- Watches Spoolman's `active_tray` assignment changes.
- Looks up the newly assigned spool and processes only its mapped Bambu tray.
- Maps the spool material and color to a Bambu filament profile.
- Calls `bambu_lab.set_filament` only when the tray's current configuration differs.
- Skips Bambu Lab branded filament, which the AMS can identify with RFID.

An assignment change triggers the update even if Bambu Lab reports the tray as empty. The Bambu integration does not reliably expose physical insertion for every tray. The integration does not open a separate MQTT connection.

## Requirements

- Home Assistant
- The Bambu Lab integration, configured for the printer
- Spoolman and Spoolman Sync, with `active_tray` assignments mapped to Bambu tray identifiers
- Network access from Home Assistant to the configured Spoolman URL

This integration uses the Spoolman URL configured during setup. It does not ask for or use an API key.

## Install with HACS

Until this repository is included in the default HACS store, add it as a custom repository:

1. In HACS, open **Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/demonkazuya/bambu-ams-spool-sync` and select **Integration** as the category.
4. Find **Bambu AMS Spool Sync**, install it, and restart Home Assistant.
5. Add the integration from **Settings → Devices & services → Add integration** and enter the Spoolman URL.


## Notes

- Keep the `custom_components/bambu_ams_spool_sync/` directory structure intact.
- A new assignment is read from Spoolman and applied to the one tray mapped by that assignment.
- Updating a spool's filament details without changing its `active_tray` assignment does not trigger a sync.
- Home Assistant may still log that this is a custom integration not tested by Home Assistant. HACS distributes community integrations; it does not make them part of Home Assistant Core.

## Issues

Report problems in the GitHub repository's issue tracker.
