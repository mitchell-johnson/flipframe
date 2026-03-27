# FlipOff.

**Turn any TV into a retro split-flap display.** The classic flip-board look, without the $3,500 hardware. And it's free.

![FlipOff Screenshot](screenshot.png)

## What is this?

FlipOff is a free, open-source web app that emulates a classic mechanical split-flap (flip-board) airport terminal display — the kind you'd see at train stations and airports. It runs full-screen in any browser, turning a TV or large monitor into a beautiful retro display.

No accounts. No subscriptions. No $199 fee. Just open `index.html` and go.

## Features

- Realistic split-flap animation with colorful scramble transitions
- Authentic mechanical clacking sound (recorded from a real split-flap display)
- Auto-rotating inspirational quotes
- Fullscreen TV mode (press `F`)
- Keyboard controls for manual navigation
- Works offline — zero external dependencies
- Responsive from mobile to 4K displays
- Pure vanilla HTML/CSS/JS — no frameworks, no build tools, no npm

### Samsung Frame TV + Weather

The CLI tool (`cli/flipframe.py`) turns FlipOff into a weather display for Samsung Frame TVs:

- Fetches weather data from Open-Meteo (free, no API key)
- Colourful weather condition icons (sun, rain, snow, thunderstorm, fog, etc.) rendered as bold SVG line art on the tiles
- Temperature numbers colour-coded by warmth — blue for cold, green for mild, orange/red for hot
- Generates 4K screenshots and uploads directly to the TV's art mode
- Schedule with cron for a daily auto-updating weather board

## Quick Start

### Browser Display

1. Clone the repo
2. Open `index.html` in a browser (or serve with any static file server)
3. Click anywhere to enable audio
4. Press `F` for fullscreen TV mode

```bash
# Or serve locally:
python3 -m http.server 8080
# Then open http://localhost:8080
```

### Samsung Frame TV (Weather Display)

```bash
# Install dependencies
pip install playwright websocket-client
playwright install chromium

# Configure your location and TV IP
cp cli/.env.example cli/.env
# Edit cli/.env with your coordinates, timezone, and TV IP

# Preview locally
python3 cli/flipframe.py preview

# Generate 4K screenshots
python3 cli/flipframe.py generate

# Push to TV art mode
python3 cli/flipframe.py push

# Schedule daily refresh (e.g. 5:30 AM)
crontab -e
# 30 5 * * * /path/to/flipoff/cli/refresh.sh
```

### Configuration

Copy `cli/.env.example` to `cli/.env` and set your values:

```bash
# Location (for weather data)
FLIPFRAME_LATITUDE=-36.85
FLIPFRAME_LONGITUDE=174.76
FLIPFRAME_TIMEZONE=Pacific/Auckland
FLIPFRAME_LOCATION=AUCKLAND, NZ

# Samsung Frame TV IP
FLIPFRAME_TV_IP=192.168.1.100
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` / `Space` | Next message |
| `Arrow Left` | Previous message |
| `Arrow Right` | Next message |
| `F` | Toggle fullscreen |
| `M` | Toggle mute |
| `Escape` | Exit fullscreen |

## How It Works

Each tile on the board is an independent element that can animate through a scramble sequence (rapid random characters with colored backgrounds) before settling on the final character. Only tiles whose content changes between messages animate — just like a real mechanical board.

The sound is a single recorded audio clip of a real split-flap transition, played once per message change to perfectly sync with the visual animation.

### Weather Icons

Weather conditions are rendered as SVG line-art icons directly on the flip tiles, matching the mechanical aesthetic:

- ☀️ Sun / clear sky — golden
- ⛅ Partly cloudy — golden with cloud
- ☁️ Overcast — grey
- 🌫️ Fog — icy blue
- 🌧️ Rain / drizzle / showers — blue/cyan
- ❄️ Snow — white-blue
- ⚡ Thunderstorm — purple

Temperature digits are coloured in fixed bands: blue (≤5°C) → cyan → teal → green → yellow → orange → red (27°C+).

## File Structure

```
flipoff/
  index.html            — Single-page app (quote display)
  kiosk.html            — Kiosk mode (data-driven, used by CLI)
  screenshot.png        — Preview image
  css/
    reset.css           — CSS reset
    layout.css          — Page layout (header, hero, board)
    board.css           — Board container and accent bars
    tile.css            — Tile styling, flip animation, weather icons
    kiosk.css           — Kiosk/TV fullscreen styles
    responsive.css      — Media queries for all screen sizes
  js/
    main.js             — Entry point and UI wiring
    Board.js            — Grid manager and transition orchestration
    Tile.js             — Individual tile animation + weather icon rendering
    SoundEngine.js      — Audio playback with Web Audio API
    MessageRotator.js   — Quote rotation timer
    KeyboardController.js — Keyboard shortcut handling
    constants.js        — Config (grid, colors, quotes, weather icons, temp bands)
    kiosk.js            — Kiosk mode entry point
    flapAudio.js        — Embedded audio data (base64)
  cli/
    flipframe.py        — CLI: generate weather content, screenshot, push to TV
    refresh.sh          — Cron wrapper for daily push
    .env.example        — Environment config template
    serve.py            — Development server
```

## Customization

Edit `js/constants.js` to change:
- **Messages**: Add your own quotes or text
- **Grid size**: Adjust `GRID_COLS` and `GRID_ROWS`
- **Timing**: Tweak `SCRAMBLE_DURATION`, `STAGGER_DELAY`, etc.
- **Colors**: Modify `SCRAMBLE_COLORS` and `ACCENT_COLORS`
- **Temperature bands**: Adjust `tempColor()` thresholds

## License

MIT — do whatever you want with it.
