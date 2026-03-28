#!/usr/bin/env python3
"""Watch Samsung Frame TV directly for power-off and switch to art mode.

Polls the TV's websocket port (8002) to detect reachable → unreachable
transitions. When the TV goes down (e.g. Apple Remote CEC power-off),
sends Wake-on-LAN and attempts to switch back to art mode.

Also refreshes weather content every 30 minutes (quiet push — no mode switch).

Run as a launchd daemon — see com.flipframe.artmode-watcher.plist
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid

# --- Config ---
TV_IP = os.environ.get("FLIPFRAME_TV_IP", "192.168.1.81")
TV_MAC = "f4:fe:fb:ae:6b:64"
TV_PORT = 8002

POLL_INTERVAL = 10         # seconds between reachability checks
POLL_TIMEOUT = 3           # seconds to wait for TCP connect
WOL_ATTEMPTS = 5           # number of WoL packets to send
WOL_RETRY_DELAY = 5        # seconds between WoL bursts
WAKE_TIMEOUT = 60          # max seconds to wait for TV to come back after WoL
COOLDOWN_SECONDS = 120     # ignore repeated off→on cycles within this window
ARTMODE_SETTLE = 15        # seconds to wait after TV reachable before art mode command
ARTMODE_RETRIES = 3        # retry art mode if TV isn't fully ready yet
ARTMODE_RETRY_DELAY = 10   # seconds between retries
REFRESH_INTERVAL = 30 * 60 # 30 minutes

CLI_DIR = os.path.dirname(os.path.abspath(__file__))
FLIPFRAME = os.path.join(CLI_DIR, "flipframe.py")


def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def tv_is_reachable():
    """Check if the TV's websocket port is accepting connections."""
    try:
        with socket.create_connection((TV_IP, TV_PORT), timeout=POLL_TIMEOUT):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def send_wol(count=1):
    """Send Wake-on-LAN magic packet(s)."""
    mac_bytes = bytes.fromhex(TV_MAC.replace(":", ""))
    magic = b"\xff" * 6 + mac_bytes * 16
    for _ in range(count):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(magic, ("255.255.255.255", 9))
            # Also send to subnet broadcast in case directed broadcast helps
            s.sendto(magic, ("192.168.1.255", 9))


def make_env():
    """Build environment with correct PATH/PYTHONPATH for subprocess calls."""
    return {
        **os.environ,
        "PATH": f"/opt/homebrew/bin:{os.environ.get('PATH', '')}",
        "PYTHONPATH": f"/Users/mitchell/Library/Python/3.14/lib/python/site-packages:{os.environ.get('PYTHONPATH', '')}",
    }


def switch_to_artmode():
    """Connect to TV and switch to art mode."""
    log("Switching to art mode...")
    try:
        result = subprocess.run(
            [sys.executable, FLIPFRAME, "artmode", "--tv-ip", TV_IP, "--timeout", "30"],
            capture_output=True, text=True, timeout=60, env=make_env(),
        )
        if result.returncode == 0:
            log(f"Art mode activated: {result.stdout.strip()}")
            return True
        else:
            log(f"Art mode failed (exit {result.returncode}): {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        log("Art mode command timed out after 60s")
        return False
    except Exception as e:
        log(f"Error running artmode: {e}")
        return False


def quiet_push():
    """Regenerate weather content and push to TV without switching to art mode."""
    if not tv_is_reachable():
        log("TV unreachable, skipping weather refresh (will retry next cycle)")
        return
    log("Refreshing weather content (quiet push)...")
    try:
        result = subprocess.run(
            [sys.executable, FLIPFRAME, "push", "--tv-ip", TV_IP, "--quiet"],
            capture_output=True, text=True, timeout=120, env=make_env(),
        )
        if result.returncode == 0:
            log(f"Weather refreshed: {result.stdout.strip().splitlines()[-1]}")
        else:
            log(f"Quiet push failed (exit {result.returncode}): {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        log("Quiet push timed out after 120s")
    except Exception as e:
        log(f"Error during quiet push: {e}")


def refresh_loop():
    """Background thread: refresh weather content every REFRESH_INTERVAL seconds."""
    log(f"Weather refresh loop started (every {REFRESH_INTERVAL // 60} min)")
    while True:
        time.sleep(REFRESH_INTERVAL)
        try:
            quiet_push()
        except Exception as e:
            log(f"Refresh loop error: {e}")


def wait_for_tv(timeout=WAKE_TIMEOUT):
    """Send WoL and wait for TV to become reachable. Returns True if TV came up."""
    log(f"Sending WoL packets and waiting up to {timeout}s for TV...")
    deadline = time.time() + timeout
    attempt = 0

    while time.time() < deadline:
        # Send WoL burst every WOL_RETRY_DELAY seconds
        if attempt % WOL_RETRY_DELAY == 0:
            wol_round = (attempt // WOL_RETRY_DELAY) + 1
            log(f"  WoL burst #{wol_round} ({WOL_ATTEMPTS} packets)")
            send_wol(count=WOL_ATTEMPTS)

        time.sleep(1)
        attempt += 1

        if tv_is_reachable():
            log(f"  TV responded after {attempt}s")
            return True

    log(f"  TV did not respond within {timeout}s")
    return False


def watch():
    """Main polling loop — detect TV going offline and switch to art mode."""
    log(f"Polling TV at {TV_IP}:{TV_PORT} every {POLL_INTERVAL}s")

    was_reachable = tv_is_reachable()
    last_artmode_time = 0
    log(f"Initial state: {'reachable' if was_reachable else 'unreachable'}")

    while True:
        time.sleep(POLL_INTERVAL)

        is_reachable = tv_is_reachable()

        # Detect transition: reachable → unreachable (TV just turned off)
        if was_reachable and not is_reachable:
            now = time.time()
            log("TV went offline (reachable → unreachable)")

            if now - last_artmode_time < COOLDOWN_SECONDS:
                remaining = int(COOLDOWN_SECONDS - (now - last_artmode_time))
                log(f"  Cooldown active ({remaining}s left), skipping art mode switch")
                was_reachable = is_reachable
                continue

            # TV just went to standby — try to wake it into art mode
            if wait_for_tv():
                # Give the TV's art channel a moment to stabilise
                log(f"  Waiting {ARTMODE_SETTLE}s for art channel to stabilise...")
                time.sleep(ARTMODE_SETTLE)

                success = False
                for attempt in range(1, ARTMODE_RETRIES + 1):
                    if switch_to_artmode():
                        success = True
                        break
                    if attempt < ARTMODE_RETRIES:
                        log(f"  Retry {attempt}/{ARTMODE_RETRIES} in {ARTMODE_RETRY_DELAY}s...")
                        time.sleep(ARTMODE_RETRY_DELAY)

                if success:
                    last_artmode_time = time.time()
                    # Push fresh weather now that we're in art mode
                    time.sleep(5)
                    quiet_push()
                else:
                    log("  Art mode switch failed after all retries")
            else:
                log("  Could not wake TV — WoL may be disabled or TV is fully powered off")

            # Re-check current state after all the waiting
            is_reachable = tv_is_reachable()

        elif not was_reachable and is_reachable:
            log("TV came online (unreachable → reachable)")

        was_reachable = is_reachable


def main():
    log("FlipFrame art mode watcher starting (direct polling mode)")

    # Start weather refresh loop in background thread
    refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
    refresh_thread.start()

    try:
        watch()
    except KeyboardInterrupt:
        log("Shutting down")
    except Exception as e:
        log(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
