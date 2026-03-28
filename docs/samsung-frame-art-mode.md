# Samsung Frame TV — Art Mode Watcher

How FlipFrame detects TV power-off and switches back to art mode.

## The Problem

When you turn off a Samsung Frame TV via Apple Remote (or any CEC source), the TV goes into **standby** — not art mode. The Frame's art mode only activates when you use the Samsung remote or the SmartThings app. This means the flip-board weather display disappears every time someone uses the Apple TV remote to power off.

## Approaches Tried

### 1. Home Assistant State Watcher (didn't work reliably)

The original approach subscribed to HA websocket `state_changed` events for the TV's `media_player` entity.

**Problem:** The Samsung HA integration relies on polling the TV over IP. When the TV enters CEC standby, it often drops off the network before HA registers the state change — or HA already has it as `off` from a previous session, so no transition event fires. The watcher would sit there subscribed to events that never come.

### 2. Direct Port Polling (current approach — works)

Poll the TV's websocket port (8002) every 10 seconds. When it transitions from **reachable → unreachable**, the TV just turned off. Then:

1. Send Wake-on-LAN magic packets to wake the TV from standby
2. Wait for port 8002 to become reachable again
3. Wait for the art channel websocket to stabilise
4. Connect and switch to art mode
5. Push fresh weather content

## Requirements

### TV Settings (must be enabled)

- **IP Remote** — Settings → General → External Device Manager → IP Remote
  - Allows network control of the TV (websocket art channel commands)
- **Network Standby / Power On with Mobile** — Settings → General → Network → Expert Settings
  - Keeps the TV's network stack alive in standby so it can respond to WoL packets
  - Without this, the TV is completely unreachable in standby and cannot be woken

### Network

- TV must have a **static IP or DHCP reservation** — the watcher polls a fixed IP
- TV MAC address must be correct in the watcher config for WoL
- Mac mini and TV must be on the **same broadcast domain** (same subnet/VLAN) for WoL

## Timing

Typical sequence after pressing power off:

| Event | Time |
|-------|------|
| TV port goes down | ~10–20s after CEC standby signal |
| Watcher detects offline | Next poll cycle (≤10s) |
| WoL wake | 1–25s depending on TV state |
| Art channel stabilise wait | 15s (fixed) |
| Art mode switch | ~7s |
| Weather push | ~25s |
| **Total** | **~60–90s from power-off to flip board showing** |

## The 2020 Frame Websocket Quirk

Samsung 2020 Frame models send `ms.channel.connect` before `ms.channel.ready` on the art channel websocket. The `samsungtvws` Python library expects `ms.channel.ready` as the first message and fails. FlipFrame's `FrameTVArt` class handles this by draining up to 5 initial events and looking for `ms.channel.ready` among them.

After a WoL wake, the TV needs extra time before the art channel is fully ready. The watcher waits 15 seconds after port 8002 becomes reachable, and retries the art mode connection up to 3 times with 10-second gaps if the channel isn't ready.

## Configuration

All config is in `cli/.env`:

```bash
FLIPFRAME_TV_IP=192.168.1.81
```

The watcher also has hardcoded defaults in `artmode-watcher.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `POLL_INTERVAL` | 10s | How often to check TV reachability |
| `WOL_ATTEMPTS` | 5 | Magic packets per burst |
| `WAKE_TIMEOUT` | 60s | Max wait for TV to come back |
| `COOLDOWN_SECONDS` | 120s | Ignore repeated off events |
| `ARTMODE_SETTLE` | 15s | Wait after TV reachable before connecting |
| `ARTMODE_RETRIES` | 3 | Retry art mode connection |
| `REFRESH_INTERVAL` | 30 min | Weather content refresh cycle |

## CEC Limitations

- **Macs cannot send HDMI-CEC commands** — there's no CEC hardware on Mac
- **pyatv** can wake an Apple TV (which triggers CEC), but only works if an Apple TV is HDMI-connected to the target TV
- The polling + WoL approach avoids CEC entirely — it's purely IP-based
