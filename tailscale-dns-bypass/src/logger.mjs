/**
 * Structured logger for tailscale-dns-bypass
 * @module logger
 *
 * Deliberately dependency-free and free of imports from other project modules:
 * `config.mjs` and `types.mjs` both log, so importing either here would create
 * a cycle at module-evaluation time.
 */

const LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };
const COLORS = {
  debug: '\x1b[36m',  // cyan
  info: '\x1b[32m',   // green
  warn: '\x1b[33m',   // yellow
  error: '\x1b[31m',  // red
  reset: '\x1b[0m'
};

let currentLevel = LEVELS.info;
let currentFormat = 'text';
let useColors = false;

/**
 * Colour output is only useful on a terminal. Honour the widely-supported
 * `NO_COLOR` convention and non-TTY streams (pipes, CI logs) instead of
 * emitting escape codes that end up as noise in a log file.
 */
function detectColorSupport() {
  if (process.env.NO_COLOR !== undefined) return false;
  if (process.env.FORCE_COLOR) return true;
  return Boolean(process.stdout && process.stdout.isTTY);
}

export function configureLogger({ level, format } = {}) {
  if (level && LEVELS[level] !== undefined) currentLevel = LEVELS[level];
  if (format) currentFormat = format;
  useColors = currentFormat !== 'json' && detectColorSupport();
}

function formatMessage(level, message, meta) {
  const timestamp = new Date().toISOString();
  const hasMeta = meta && Object.keys(meta).length > 0;

  if (currentFormat === 'json') {
    const record = { timestamp, level, message, ...(hasMeta ? meta : {}) };
    try {
      return JSON.stringify(record);
    } catch {
      // Circular or otherwise unserialisable metadata. Still emit valid JSON so
      // downstream log parsers do not choke on a broken line.
      return JSON.stringify({
        timestamp,
        level,
        message,
        meta: '[unserializable]',
        error: 'metadata could not be serialized'
      });
    }
  }

  const color = useColors ? (COLORS[level] || '') : '';
  const reset = useColors ? COLORS.reset : '';
  let metaStr = '';
  if (hasMeta) {
    try {
      metaStr = ' ' + JSON.stringify(meta).replace(/\s+/g, ' ');
    } catch {
      metaStr = ' [unserializable]';
    }
  }
  return `${color}[${timestamp}] ${level.toUpperCase()}${reset} ${message}${metaStr}`;
}

export function debug(message, meta) {
  if (currentLevel <= LEVELS.debug) console.debug(formatMessage('debug', message, meta));
}

export function info(message, meta) {
  if (currentLevel <= LEVELS.info) console.info(formatMessage('info', message, meta));
}

export function warn(message, meta) {
  if (currentLevel <= LEVELS.warn) console.warn(formatMessage('warn', message, meta));
}

export function error(message, meta) {
  if (currentLevel <= LEVELS.error) console.error(formatMessage('error', message, meta));
}

export function createChildLogger(defaultMeta) {
  return {
    debug: (msg, meta) => debug(msg, { ...defaultMeta, ...meta }),
    info: (msg, meta) => info(msg, { ...defaultMeta, ...meta }),
    warn: (msg, meta) => warn(msg, { ...defaultMeta, ...meta }),
    error: (msg, meta) => error(msg, { ...defaultMeta, ...meta })
  };
}