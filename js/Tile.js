import { CHARSET, SCRAMBLE_COLORS, SCRAMBLE_DURATION, FLIP_DURATION, WEATHER_ICONS, decodeTempDigit, tempColor } from './constants.js';

// SVG path data for weather icons (designed to fill a tile, bold stencil style)
const ICON_SVGS = {
  'sun': `<circle cx="50" cy="50" r="18" fill="none" stroke="currentColor" stroke-width="5"/>
    <line x1="50" y1="8" x2="50" y2="22" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="50" y1="78" x2="50" y2="92" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="8" y1="50" x2="22" y2="50" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="78" y1="50" x2="92" y2="50" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="20" y1="20" x2="30" y2="30" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="70" y1="70" x2="80" y2="80" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="80" y1="20" x2="70" y2="30" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="30" y1="70" x2="20" y2="80" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>`,

  'partly-cloudy': `<circle cx="38" cy="38" r="14" fill="none" stroke="currentColor" stroke-width="4.5"/>
    <line x1="38" y1="10" x2="38" y2="19" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
    <line x1="14" y1="28" x2="21" y2="31" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
    <line x1="18" y1="14" x2="24" y2="22" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
    <path d="M30 72 Q30 56 44 54 Q44 42 58 42 Q72 42 74 54 Q86 56 86 66 Q86 72 80 72 Z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/>`,

  'overcast': `<path d="M18 72 Q18 54 34 50 Q36 36 52 36 Q68 36 70 50 Q84 52 84 64 Q84 72 76 72 Z" fill="none" stroke="currentColor" stroke-width="5" stroke-linejoin="round"/>
    <path d="M32 52 Q32 40 44 38 Q46 28 58 28 Q70 28 72 38 Q82 40 82 48" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round" opacity="0.5"/>`,

  'fog': `<line x1="16" y1="34" x2="84" y2="34" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="22" y1="48" x2="78" y2="48" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="16" y1="62" x2="84" y2="62" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
    <line x1="28" y1="76" x2="72" y2="76" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>`,

  'drizzle': `<path d="M20 52 Q20 38 34 34 Q36 24 48 24 Q60 24 62 34 Q74 36 74 46 Q74 52 68 52 Z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/>
    <line x1="32" y1="60" x2="30" y2="70" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="50" y1="60" x2="48" y2="70" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="68" y1="60" x2="66" y2="70" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>`,

  'rain': `<path d="M18 50 Q18 36 32 32 Q34 22 48 22 Q62 22 64 32 Q76 34 76 44 Q76 50 70 50 Z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/>
    <line x1="28" y1="58" x2="24" y2="72" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
    <line x1="42" y1="58" x2="38" y2="72" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
    <line x1="56" y1="58" x2="52" y2="72" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
    <line x1="70" y1="58" x2="66" y2="72" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>`,

  'heavy-rain': `<path d="M18 46 Q18 32 32 28 Q34 18 48 18 Q62 18 64 28 Q76 30 76 40 Q76 46 70 46 Z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/>
    <line x1="26" y1="54" x2="20" y2="72" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
    <line x1="40" y1="54" x2="34" y2="72" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
    <line x1="54" y1="54" x2="48" y2="72" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
    <line x1="68" y1="54" x2="62" y2="72" stroke="currentColor" stroke-width="4.5" stroke-linecap="round"/>
    <line x1="33" y1="74" x2="29" y2="86" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
    <line x1="54" y1="74" x2="50" y2="86" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>`,

  'snow': `<path d="M20 50 Q20 36 34 32 Q36 22 48 22 Q60 22 62 32 Q74 34 74 44 Q74 50 68 50 Z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/>
    <circle cx="32" cy="64" r="3.5" fill="currentColor"/>
    <circle cx="48" cy="60" r="3.5" fill="currentColor"/>
    <circle cx="64" cy="64" r="3.5" fill="currentColor"/>
    <circle cx="40" cy="76" r="3.5" fill="currentColor"/>
    <circle cx="56" cy="76" r="3.5" fill="currentColor"/>`,

  'thunderstorm': `<path d="M18 46 Q18 32 32 28 Q34 18 48 18 Q62 18 64 28 Q76 30 76 40 Q76 46 70 46 Z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/>
    <polygon points="44,50 36,68 46,68 38,88 60,62 48,62 56,50" fill="currentColor"/>`,

  'showers': `<path d="M20 50 Q20 36 34 32 Q36 22 48 22 Q60 22 62 32 Q74 34 74 44 Q74 50 68 50 Z" fill="none" stroke="currentColor" stroke-width="4.5" stroke-linejoin="round"/>
    <line x1="30" y1="58" x2="28" y2="68" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="48" y1="56" x2="46" y2="66" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="64" y1="60" x2="62" y2="70" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="38" y1="70" x2="36" y2="80" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="56" y1="68" x2="54" y2="78" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>`,
};

export class Tile {
  constructor(row, col) {
    this.row = row;
    this.col = col;
    this.currentChar = ' ';
    this.isAnimating = false;
    this._scrambleTimer = null;

    // Build DOM
    this.el = document.createElement('div');
    this.el.className = 'tile';

    this.innerEl = document.createElement('div');
    this.innerEl.className = 'tile-inner';

    this.frontEl = document.createElement('div');
    this.frontEl.className = 'tile-front';
    this.frontSpan = document.createElement('span');
    this.frontEl.appendChild(this.frontSpan);

    this.backEl = document.createElement('div');
    this.backEl.className = 'tile-back';
    this.backSpan = document.createElement('span');
    this.backEl.appendChild(this.backSpan);

    this.innerEl.appendChild(this.frontEl);
    this.innerEl.appendChild(this.backEl);
    this.el.appendChild(this.innerEl);
  }

  setChar(char) {
    this.currentChar = char;
    this._clearIcon(this.frontEl);
    this.frontEl.style.backgroundColor = '';
    this.frontSpan.style.color = '';

    const icon = WEATHER_ICONS[char];
    const td = decodeTempDigit(char);
    if (icon && ICON_SVGS[icon.name]) {
      this.frontSpan.textContent = '';
      this._renderIcon(this.frontEl, icon);
    } else if (td) {
      this.frontSpan.textContent = String(td.digit);
      this.frontSpan.style.color = tempColor(td.temp);
    } else {
      this.frontSpan.textContent = char === ' ' ? '' : char;
    }
    this.backSpan.textContent = '';
  }

  _renderIcon(faceEl, icon) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('class', 'weather-icon');
    svg.style.color = icon.color;
    svg.innerHTML = ICON_SVGS[icon.name];
    faceEl.appendChild(svg);
  }

  _clearIcon(faceEl) {
    const existing = faceEl.querySelector('.weather-icon');
    if (existing) existing.remove();
  }

  scrambleTo(targetChar, delay) {
    if (targetChar === this.currentChar) return;

    // Cancel any in-progress animation
    if (this._scrambleTimer) {
      clearInterval(this._scrambleTimer);
      this._scrambleTimer = null;
    }
    this.isAnimating = true;

    setTimeout(() => {
      this.el.classList.add('scrambling');
      let scrambleCount = 0;
      const maxScrambles = 10 + Math.floor(Math.random() * 4);
      const scrambleInterval = 70;

      this._scrambleTimer = setInterval(() => {
        // Random character
        const randChar = CHARSET[Math.floor(Math.random() * CHARSET.length)];
        this.frontSpan.textContent = randChar === ' ' ? '' : randChar;

        // Cycle background color
        const color = SCRAMBLE_COLORS[scrambleCount % SCRAMBLE_COLORS.length];
        this.frontEl.style.backgroundColor = color;

        // Briefly change text color for contrast on light backgrounds
        if (color === '#FFFFFF' || color === '#FFCC00') {
          this.frontSpan.style.color = '#111';
        } else {
          this.frontSpan.style.color = '';
        }

        scrambleCount++;

        if (scrambleCount >= maxScrambles) {
          clearInterval(this._scrambleTimer);
          this._scrambleTimer = null;

          // Reset colors
          this.frontEl.style.backgroundColor = '';
          this.frontSpan.style.color = '';

          // Set the final character directly (skip 3D flip for reliability)
          // Use a brief opacity flash to simulate the flip settle
          this._clearIcon(this.frontEl);
          this.frontSpan.style.color = '';
          const targetIcon = WEATHER_ICONS[targetChar];
          const targetTd = decodeTempDigit(targetChar);
          if (targetIcon && ICON_SVGS[targetIcon.name]) {
            this.frontSpan.textContent = '';
            this._renderIcon(this.frontEl, targetIcon);
          } else if (targetTd) {
            this.frontSpan.textContent = String(targetTd.digit);
            this.frontSpan.style.color = tempColor(targetTd.temp);
          } else {
            this.frontSpan.textContent = targetChar === ' ' ? '' : targetChar;
          }

          // Quick flash effect: brief scale transform
          this.innerEl.style.transition = `transform ${FLIP_DURATION}ms ease-in-out`;
          this.innerEl.style.transform = 'perspective(400px) rotateX(-8deg)';

          setTimeout(() => {
            this.innerEl.style.transform = '';
            setTimeout(() => {
              this.innerEl.style.transition = '';
              this.el.classList.remove('scrambling');
              this.currentChar = targetChar;
              this.isAnimating = false;
            }, FLIP_DURATION);
          }, FLIP_DURATION / 2);
        }
      }, scrambleInterval);
    }, delay);
  }
}
