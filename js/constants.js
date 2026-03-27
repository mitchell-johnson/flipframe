export const GRID_COLS = 30;
export const GRID_ROWS = 5;

export const SCRAMBLE_DURATION = 800;
export const FLIP_DURATION = 300;
export const STAGGER_DELAY = 25;
export const TOTAL_TRANSITION = 3800;
export const MESSAGE_INTERVAL = 4000;

export const CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,-!?\'/: ';

// Weather icon character codes (Unicode Private Use Area)
// Used by flipframe.py content generator → rendered as SVG in Tile.js
// Temperature-colored digits: PUA range \uE100–\uE28F
// Encoding: code = 0xE100 + (temp * 10) + digit
// temp 0 = full blue (#00AAFF), temp 30 = full red (#FF2D00)
export const TEMP_DIGIT_BASE = 0xE100;
export const TEMP_DIGIT_END = 0xE290;  // 40 temps * 10 digits

export function decodeTempDigit(char) {
  const code = char.charCodeAt(0);
  if (code < TEMP_DIGIT_BASE || code >= TEMP_DIGIT_END) return null;
  const offset = code - TEMP_DIGIT_BASE;
  const digit = offset % 10;
  const temp = Math.floor(offset / 10);
  return { digit, temp };
}

export function tempColor(temp) {
  // Fixed color bands
  if (temp <= 5)  return '#00AAFF'; // cold blue
  if (temp <= 10) return '#00CCFF'; // cool cyan
  if (temp <= 14) return '#00DDAA'; // teal
  if (temp <= 18) return '#66DD44'; // green
  if (temp <= 22) return '#FFCC00'; // warm yellow
  if (temp <= 26) return '#FF8800'; // orange
  return '#FF2D00';                 // hot red
}

export const WEATHER_ICONS = {
  '\uE001': { name: 'sun',           color: '#FFCC00' },
  '\uE002': { name: 'partly-cloudy', color: '#FFCC00' },
  '\uE003': { name: 'overcast',      color: '#888888' },
  '\uE004': { name: 'fog',           color: '#BBCCDD' },
  '\uE005': { name: 'drizzle',       color: '#66CCFF' },
  '\uE006': { name: 'rain',          color: '#00AAFF' },
  '\uE007': { name: 'heavy-rain',    color: '#0077DD' },
  '\uE008': { name: 'snow',          color: '#CCDDFF' },
  '\uE009': { name: 'thunderstorm',  color: '#AA00FF' },
  '\uE00A': { name: 'showers',       color: '#00CCFF' },
};

export const SCRAMBLE_COLORS = [
  '#00AAFF', '#00FFCC', '#AA00FF',
  '#FF2D00', '#FFCC00', '#FFFFFF'
];

export const ACCENT_COLORS = [
  '#00FF7F', '#FF4D00', '#AA00FF',
  '#00AAFF', '#00FFCC'
];

export const MESSAGES = [
  [
    '',
    'GOD IS IN',
    'THE DETAILS .',
    '- LUDWIG MIES',
    ''
  ],
  [
    '',
    'STAY HUNGRY',
    'STAY FOOLISH',
    '- STEVE JOBS',
    ''
  ],
  [
    '',
    'GOOD DESIGN IS',
    'GOOD BUSINESS',
    '- THOMAS WATSON',
    ''
  ],
  [
    '',
    'LESS IS MORE',
    '',
    '- MIES VAN DER ROHE',
    ''
  ],
  [
    '',
    'MAKE IT SIMPLE',
    'BUT SIGNIFICANT',
    '- DON DRAPER',
    ''
  ],
  [
    '',
    'HAVE NO FEAR OF',
    'PERFECTION',
    '- SALVADOR DALI',
    ''
  ]
];
