#!/usr/bin/env python3
"""FlipFrame — Split-flap display content generator for Samsung Frame TV."""

import argparse
import asyncio
import base64
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# --- Paths ---
CLI_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CLI_DIR.parent
OUTPUT_DIR = CLI_DIR / "output"
TOKEN_FILE = CLI_DIR / ".tv-token"

# Auckland NZ
LATITUDE = -36.85
LONGITUDE = 174.76
TIMEZONE = "Pacific/Auckland"
DEFAULT_TV_IP = "192.168.1.81"

# --- WMO Weather Codes ---
WMO_CODES = {
    0: "CLEAR SKY",
    1: "MAINLY CLEAR",
    2: "PARTLY CLOUDY",
    3: "OVERCAST",
    45: "FOG",
    48: "FREEZING FOG",
    51: "LIGHT DRIZZLE",
    53: "DRIZZLE",
    55: "HEAVY DRIZZLE",
    56: "FREEZING DRIZZLE",
    57: "HEAVY FREEZING DRIZZLE",
    61: "LIGHT RAIN",
    63: "RAIN",
    65: "HEAVY RAIN",
    66: "FREEZING RAIN",
    67: "HEAVY FREEZING RAIN",
    71: "LIGHT SNOW",
    73: "SNOW",
    75: "HEAVY SNOW",
    77: "SNOW GRAINS",
    80: "LIGHT SHOWERS",
    81: "SHOWERS",
    82: "HEAVY SHOWERS",
    85: "LIGHT SNOW SHOWERS",
    86: "HEAVY SNOW SHOWERS",
    95: "THUNDERSTORM",
    96: "THUNDERSTORM W/ HAIL",
    99: "SEVERE THUNDERSTORM",
}


def wind_direction_str(degrees):
    """Convert wind direction degrees to compass abbreviation."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = round(degrees / 45) % 8
    return dirs[idx]


def fetch_weather():
    """Fetch 2-day forecast from Open-Meteo API (free, no key needed)."""
    params = urllib.parse.urlencode({
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "weathercode",
            "windspeed_10m_max",
            "winddirection_10m_dominant",
            "precipitation_probability_max",
        ]),
        "timezone": TIMEZONE,
        "forecast_days": 2,
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"

    print("Fetching weather data...")
    req = urllib.request.Request(url, headers={"User-Agent": "FlipFrame/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def generate_content(weather_data=None):
    """Build content pages JSON from weather data."""
    if weather_data:
        today_str = weather_data["daily"]["time"][0]
        today_date = datetime.strptime(today_str, "%Y-%m-%d")
        tomorrow_date = datetime.strptime(weather_data["daily"]["time"][1], "%Y-%m-%d")
    else:
        today_date = datetime.now()
        tomorrow_date = today_date + timedelta(days=1)

    day_name = today_date.strftime("%A").upper()
    month_name = today_date.strftime("%B").upper()
    day_num = today_date.day
    year = today_date.year

    # Page 1: Date
    page1 = {
        "lines": [
            day_name,
            f"{month_name} {day_num}, {year}",
            "",
            "AUCKLAND, NZ",
            "",
            "",
        ]
    }

    pages = [page1]

    if weather_data:
        daily = weather_data["daily"]

        # Page 2: Today's weather
        t_high = round(daily["temperature_2m_max"][0])
        t_low = round(daily["temperature_2m_min"][0])
        t_code = daily["weathercode"][0]
        t_wind = round(daily["windspeed_10m_max"][0])
        t_wdir = wind_direction_str(daily["winddirection_10m_dominant"][0])
        t_rain = round(daily["precipitation_probability_max"][0])
        t_desc = WMO_CODES.get(t_code, "UNKNOWN")
        t_short = today_date.strftime("%a %d %b").upper()

        pages.append({
            "lines": [
                f"TODAY  {t_short}",
                f"HIGH {t_high}  LOW {t_low}",
                t_desc,
                f"WIND {t_wind} KM/H {t_wdir}",
                f"RAIN {t_rain}%",
                "",
            ]
        })

        # Page 3: Tomorrow's weather
        m_high = round(daily["temperature_2m_max"][1])
        m_low = round(daily["temperature_2m_min"][1])
        m_code = daily["weathercode"][1]
        m_wind = round(daily["windspeed_10m_max"][1])
        m_wdir = wind_direction_str(daily["winddirection_10m_dominant"][1])
        m_rain = round(daily["precipitation_probability_max"][1])
        m_desc = WMO_CODES.get(m_code, "UNKNOWN")
        m_short = tomorrow_date.strftime("%a %d %b").upper()

        pages.append({
            "lines": [
                f"TOMORROW  {m_short}",
                f"HIGH {m_high}  LOW {m_low}",
                m_desc,
                f"WIND {m_wind} KM/H {m_wdir}",
                f"RAIN {m_rain}%",
                "",
            ]
        })

    return {"pages": pages, "interval": 15000}


class QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler that suppresses request logs."""

    def log_message(self, format, *args):
        pass


def start_server(port=8765):
    """Start a local HTTP server serving the project directory."""
    os.chdir(PROJECT_DIR)
    httpd = HTTPServer(("127.0.0.1", port), QuietHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def build_kiosk_url(content, port=8765):
    """Build kiosk URL with content encoded as base64 data param."""
    data_b64 = base64.b64encode(json.dumps(content).encode()).decode()
    return f"http://127.0.0.1:{port}/kiosk.html?data={data_b64}"


async def capture_screenshots(content, port=8765):
    """Capture 4K screenshots of each content page using Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Error: playwright not installed.")
        print("  pip install playwright && playwright install chromium")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Use a very long interval so auto-advance doesn't interfere
    frozen = {**content, "interval": 999999}
    url = build_kiosk_url(frozen, port)

    screenshots = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 3840, "height": 2160},
            device_scale_factor=1,
        )

        await page.goto(url)
        await page.wait_for_function("window.flipframe !== undefined", timeout=10000)

        total_pages = await page.evaluate("window.flipframe.getTotalPages()")
        print(f"Capturing {total_pages} page(s) at 3840x2160...")

        for i in range(total_pages):
            if i > 0:
                await page.evaluate("window.flipframe.nextPage()")

            # Wait for transition to finish
            await page.wait_for_function(
                "!window.flipframe.isTransitioning()",
                timeout=15000,
            )
            # Let animations fully settle
            await page.wait_for_timeout(800)

            filename = f"flipframe_{i + 1}.png"
            filepath = OUTPUT_DIR / filename
            await page.screenshot(path=str(filepath))
            screenshots.append(filepath)
            print(f"  Captured: {filename}")

        await browser.close()

    return screenshots


def push_to_tv(screenshots, tv_ip):
    """Upload screenshots to Samsung Frame TV art mode."""
    try:
        from samsungtvws import SamsungTVWS
    except ImportError:
        print("Error: samsungtvws not installed.")
        print("  pip install samsungtvws")
        sys.exit(1)

    token_file = str(TOKEN_FILE)

    print(f"Connecting to TV at {tv_ip}...")
    try:
        tv = SamsungTVWS(host=tv_ip, port=8002, token_file=token_file)
        tv.open()
    except Exception as e:
        print(f"Could not connect to TV at {tv_ip}: {e}")
        print("Is the TV on and connected to the network?")
        sys.exit(1)

    uploaded = []
    try:
        art = tv.art()

        for ss in screenshots:
            print(f"  Uploading {ss.name}...")
            data = ss.read_bytes()
            result = art.upload(data, file_type="PNG", matte="none")
            uploaded.append(result)
            print(f"    Content ID: {result}")

        if uploaded:
            art.select_image(uploaded[0], show=True)
            print("Set first image as current art")

        if len(uploaded) > 1:
            try:
                art.set_slideshow(uploaded, category="MY-C0004", interval=15)
                print(f"Slideshow configured: {len(uploaded)} images, 15s interval")
            except Exception:
                print("Note: Auto-slideshow not available on this TV model")
                print("  Images uploaded — configure slideshow via TV remote")

    except Exception as e:
        print(f"Upload error: {e}")
        sys.exit(1)
    finally:
        try:
            tv.close()
        except Exception:
            pass

    return uploaded


# --- Commands ---


def cmd_push(args):
    """Generate content, capture screenshots, and push to TV."""
    weather = fetch_weather()
    content = generate_content(weather)
    print(f"Generated {len(content['pages'])} page(s)")

    port = 8765
    httpd = start_server(port)
    print(f"Local server on port {port}")

    try:
        screenshots = asyncio.run(capture_screenshots(content, port))
        push_to_tv(screenshots, args.tv_ip)
        print("\nDone! Your Frame TV should now display the split-flap content.")
    finally:
        httpd.shutdown()


def cmd_preview(args):
    """Open kiosk page in default browser for preview."""
    weather = None
    try:
        weather = fetch_weather()
    except Exception as e:
        print(f"Warning: Could not fetch weather ({e}), using date only")

    content = generate_content(weather)

    port = 8765
    httpd = start_server(port)
    url = build_kiosk_url(content, port)

    print(f"Opening: {url}")
    webbrowser.open(url)

    print("Press Ctrl+C to stop the server")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.shutdown()


def cmd_generate(args):
    """Generate 4K screenshots to cli/output/."""
    weather = fetch_weather()
    content = generate_content(weather)
    print(f"Generated {len(content['pages'])} page(s)")

    port = 8765
    httpd = start_server(port)

    try:
        screenshots = asyncio.run(capture_screenshots(content, port))
        print(f"\nScreenshots saved to: {OUTPUT_DIR}")
        for s in screenshots:
            print(f"  {s}")
    finally:
        httpd.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description="FlipFrame — Split-flap display for Samsung Frame TV",
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    push_p = sub.add_parser("push", help="Generate & push to TV")
    push_p.add_argument(
        "--tv-ip",
        default=DEFAULT_TV_IP,
        help=f"TV IP address (default: {DEFAULT_TV_IP})",
    )

    sub.add_parser("preview", help="Open in browser for preview")
    sub.add_parser("generate", help="Generate screenshots only (to cli/output/)")

    args = parser.parse_args()

    if args.command == "push":
        cmd_push(args)
    elif args.command == "preview":
        cmd_preview(args)
    elif args.command == "generate":
        cmd_generate(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
