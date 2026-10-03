# Aquanix ST-101 — Home Assistant integration

Monitor an **Aquanix ST-101** auto top-off (ATO) controller from Home
Assistant, without the vendor's Android app running.

The ST-101 doesn't expose a local API. It reports its status (most notably
*reservoir empty*) by pushing a message to the vendor's cloud, which the
official app polls and displays. This integration polls the same endpoint.

## Why not just decompile the app

The vendor's `com.aquanix.main` app is built with **Delphi / FireMonkey**
(Embarcadero), not Java or Kotlin — its actual logic lives in natively
compiled code, not in the APK's `.dex` files, so static decompilation (jadx,
apktool) turns up only Delphi's own Android runtime shim, nothing
app-specific. The API shape below was recovered instead from a **mitmproxy**
capture of the app's own traffic.

## What it exposes

| Entity | Platform | Meaning |
|---|---|---|
| Aquanix Son Mesaj | `sensor` | Latest message text, or `OK` when none |
| Aquanix Hazne Durumu | `binary_sensor` (`problem`) | On when a message (e.g. reservoir empty) is active |

A message is left on the vendor's server for up to 24 hours after it's first
seen, then this integration deletes it automatically. You can also call
`aquanix.delete_message` to clear it immediately (optionally scoped to one
device via its config entry ID).

## How the API works

```
GET {BASE_URL}/device/mesajlari_oku?sifre={password}&device_id={device_id}
GET {BASE_URL}/device/delete?sifre={password}&id={message_id}
```

with `BASE_URL = https://deselbulut.com/aquanix-sistem/public/api` and a
fixed `Authorization: Basic …` header. That header is the vendor app's own
shared credential — every installation of the official app sends the same
value — not a per-device secret; your device is identified by `device_id` /
`sifre` alone, which you get from a mitmproxy capture of the app (see
below).

- No messages: the endpoint returns `{"MessageText": "Kayit_yok"}`
- A message present: a one-item JSON array with `ID`, `MessageText`,
  `DateTime`

## Capturing your device's credentials

1. Install [mitmproxy](https://mitmproxy.org/) and point your phone's Wi-Fi
   proxy at it (or run it on a laptop both devices share a network with).
2. Trust mitmproxy's CA on the phone (`http://mitm.it`), since the app's
   traffic is HTTPS.
3. Open the Aquanix app and let it refresh the device status.
4. In mitmproxy, find the request to `.../device/mesajlari_oku` and read off
   the `device_id` and `sifre` query parameters.

## Install

Needs Home Assistant **2024.12 or newer**. Copy
`custom_components/aquanix/` into your Home Assistant `config` directory,
restart, then **Settings → Devices & Services → Add Integration → Aquanix
ST-101** and enter the `device_id` / password from the capture above.
Installable through [HACS](https://hacs.xyz/) as a custom repository.

The polling interval (default 60s) can be changed afterwards from the
integration's **Configure** option, without re-adding it.

## Changelog highlights (1.1.0)

- Fixed: a failed delete after the 24h window no longer makes the sensor
  briefly report `OK` while the underlying alert is still active.
- Added an options flow to change the polling interval after setup.
- Added reauthentication: a rejected password now prompts for a new one
  instead of leaving the integration silently broken.
- `aquanix.delete_message` now respects `entry_id` when given, instead of
  always acting on every configured device.
- Switched to Home Assistant's shared HTTP session instead of opening a new
  one per request.

## Scope

Read-only monitoring of the ST-101's alert messages. The ST-101 itself has
no further controllable settings exposed through this cloud API.
