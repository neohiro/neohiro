/* LANScan dashboard — local-only instrument panel.
 *
 * Contract
 *   - Renders a "snapshot" produced by the LANScan service on the user's own
 *     machine. Schema: schema/snapshot.schema.json (schema_version 1).
 *   - No third-party requests, ever. The only network peer is the endpoint the
 *     user typed in (loopback by default). Fonts are system fonts, icons are
 *     inline SVG, there is no analytics and no CDN.
 *   - Persistence is localStorage only, so a refresh keeps the last snapshot.
 *     RESET clears it.
 */
'use strict';

(function () {

  /* ============================================================ constants */

  var STORE_KEY = 'lanscan.state.v1';
  var SNAP_KEY = 'lanscan.snapshot.v1';
  var DEFAULT_ENDPOINT = 'http://127.0.0.1:8787';
  var STALE_MS = 15000;
  var TIP_MS = 1500;
  var MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

  /* Ports probed when the user has not given an explicit endpoint. Order is
   * deliberate: the documented default first, then the alternate. Probing is
   * loopback-only and each attempt is short. */
  var CANDIDATE_PORTS = [8787, 8788, 8765];

  /* ================================================================ state */

  var state = {
    endpoint: DEFAULT_ENDPOINT,
    interval: 2000,
    paused: false,
    demo: false,
    snapshot: null,
    lastOk: 0,
    lastErr: '',
    inflight: false,
    timer: null,
    probing: false,
    seen: Object.create(null)   /* mac|serial|driver -> last value, for the "changed" flash */
  };

  /* ================================================================ utils */

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = String(txt);
    return n;
  }

  function no(s) {
    if (s === null || s === undefined) return '';
    s = String(s).trim();
    return (s === 'null' || s === 'undefined' || s === '-') ? '' : s;
  }

  function num(v) {
    var n = typeof v === 'number' ? v : parseFloat(v);
    return isFinite(n) ? n : null;
  }

  function bytes(n) {
    n = num(n);
    if (n === null) return '';
    var u = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'], i = 0, v = Math.abs(n);
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return (n < 0 ? '-' : '') + (v >= 100 || i === 0 ? v.toFixed(0) : v.toFixed(1)) + ' ' + u[i];
  }

  function bits(n) {
    n = num(n);
    if (n === null) return '';
    var u = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps'], i = 0, v = Math.abs(n);
    while (v >= 1000 && i < u.length - 1) { v /= 1000; i++; }
    return (n < 0 ? '-' : '') + (v >= 100 || i === 0 ? v.toFixed(0) : v.toFixed(1)) + ' ' + u[i];
  }

  function ms(v) {
    var n = num(v);
    if (n === null) return '';
    if (n < 1) return n.toFixed(2) + ' ms';
    if (n < 100) return n.toFixed(1) + ' ms';
    return n.toFixed(0) + ' ms';
  }

  function dur(sec) {
    var n = num(sec);
    if (n === null) return '';
    n = Math.floor(n);
    var d = Math.floor(n / 86400), h = Math.floor((n % 86400) / 3600),
        m = Math.floor((n % 3600) / 60), s = n % 60, out = [];
    if (d) out.push(d + 'd');
    if (d || h) out.push(h + 'h');
    if (d || h || m) out.push(m + 'm');
    out.push(s + 's');
    return out.join(' ');
  }

  function ago(iso) {
    var t = Date.parse(iso);
    if (!isFinite(t)) return '';
    var s = Math.max(0, (Date.now() - t) / 1000);
    if (s < 45) return 'just now';
    if (s < 3600) return Math.round(s / 60) + 'm ago';
    if (s < 86400) return Math.round(s / 3600) + 'h ago';
    return Math.round(s / 86400) + 'd ago';
  }

  function clockTime(iso) {
    var t = Date.parse(iso);
    if (!isFinite(t)) return '';
    var d = new Date(t);
    return String(d.getHours()).padStart(2, '0') + ':' +
           String(d.getMinutes()).padStart(2, '0') + ':' +
           String(d.getSeconds()).padStart(2, '0');
  }

  function titleize(s) {
    s = no(s).replace(/[_.:-]+/g, ' ').trim();
    if (!s) return '';
    return s.replace(/\b[a-z]/g, function (c) { return c.toUpperCase(); });
  }

  /* ============================================================== storage */

  function store(key) {
    try {
      var v = window.localStorage.getItem(key);
      return v ? JSON.parse(v) : null;
    } catch (e) { return null; }
  }

  function setStore(key, val) {
    try {
      window.localStorage.setItem(key, JSON.stringify(val));
      return true;
    } catch (e) {
      /* QuotaExceeded or storage disabled (private mode / file:// in some
       * browsers). The dashboard stays fully usable in memory. */
      return false;
    }
  }

  function dropStore(key) {
    try { window.localStorage.removeItem(key); } catch (e) {}
  }

  function savePrefs() {
    setStore(STORE_KEY, {
      endpoint: state.endpoint,
      interval: state.interval,
      paused: state.paused,
      demo: state.demo
    });
  }

  function loadPrefs() {
    var p = store(STORE_KEY);
    if (!p || typeof p !== 'object') return;
    if (typeof p.endpoint === 'string' && p.endpoint) state.endpoint = p.endpoint;
    if (num(p.interval) >= 500) state.interval = num(p.interval);
    if (typeof p.paused === 'boolean') state.paused = p.paused;
    if (typeof p.demo === 'boolean') state.demo = p.demo;
  }

  /* ============================================================== tooltip */

  var tipEl = $('tip');
  var tipTimer = null;

  function tip(msg, kind) {
    if (!tipEl || !msg) return;
    tipEl.textContent = msg;
    tipEl.className = 'tip on' + (kind ? ' ' + kind : '');
    if (tipTimer) clearTimeout(tipTimer);
    tipTimer = setTimeout(function () {
      tipEl.className = 'tip';
    }, TIP_MS);
  }

  /* ================================================================ copy */

  function copyText(text, label) {
    if (!text) { tip('nothing to copy', 'err'); return; }
    var done = function () { tip((label ? label + ' ' : '') + 'copied!', 'ok'); };
    var fail = function () { tip('copy blocked — select it manually', 'err'); };

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { legacy(text, done, fail); });
    } else {
      legacy(text, done, fail);
    }
  }

  /* clipboard API is unavailable on plain http://127.0.0.1 in some browsers
   * (and on file://), so keep the textarea path as a real fallback. */
  function legacy(text, done, fail) {
    try {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none';
      document.body.appendChild(ta);
      ta.select();
      ta.setSelectionRange(0, text.length);
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      ok ? done() : fail();
    } catch (e) { fail(); }
  }

  /* Build the clipboard payload for a whole record. Plain `key: value` lines so
   * it pastes cleanly into a terminal, a ticket, or a spreadsheet. */
  function recordText(title, pairs) {
    var out = [title], width = 0, i;
    for (i = 0; i < pairs.length; i++) {
      width = Math.max(width, no(pairs[i][0]).length);
    }
    for (i = 0; i < pairs.length; i++) {
      var k = no(pairs[i][0]), v = no(pairs[i][1]);
      if (!v) continue;
      out.push(k + ':' + new Array(width - k.length + 3).join(' ') + v);
    }
    return out.join('\n');
  }

  /* ============================================================= rendering */

  var LAN_EDGE_KINDS = {
    'gateway': 'gw', 'router': 'edge', 'firewall': 'edge', 'nas': 'edge',
    'switch': 'edge', 'ap': 'edge', 'access point': 'edge', 'modem': 'edge',
    'onion': 'edge', 'camera': 'iot', 'printer': 'iot', 'tv': 'iot',
    'console': 'iot', 'speaker': 'iot', 'hub': 'iot', 'sensor': 'iot'
  };

  function edgeTag(kind, isGw) {
    if (isGw) return ['tag tag-gw', 'GATEWAY'];
    var k = no(kind).toLowerCase();
    if (LAN_EDGE_KINDS[k]) return ['tag tag-' + LAN_EDGE_KINDS[k], k.toUpperCase()];
    return null;
  }

  /* A copyable metric. Left click copies just this value. */
  function metric(label, value, cls) {
    var v = no(value);
    var b = el('button', 'm' + (cls ? ' ' + cls : ''));
    b.type = 'button';
    b.textContent = v || '—';
    if (!v) { b.classList.add('m-dim'); b.disabled = true; b.style.cursor = 'default'; }
    b.dataset.label = no(label) || 'value';
    b.dataset.val = v;
    b.title = v ? 'Copy ' + label : no(label);
    return b;
  }

  /* Mark values that changed since the previous render. */
  function flash(node, key, value) {
    if (!key) return;
    var prev = state.seen[key];
    if (prev !== undefined && prev !== value) {
      node.classList.add('m-fresh');
      setTimeout(function () { node.classList.remove('m-fresh'); }, 1200);
    }
    state.seen[key] = value;
  }

  function pill(kind, text) { return el('span', 'pill p-' + kind, text); }

  function updateCell(cell, u) {
    cell.textContent = '';
    if (!u || u.available === undefined || u.available === null) {
      var s = el('span', 'upd u-na', u && no(u.current) ? no(u.current) : '—');
      cell.appendChild(s);
      return;
    }
    if (!u.available) {
      cell.appendChild(el('span', 'upd u-none', no(u.current) || 'current'));
      return;
    }
    var w = el('span', 'upd u-yes', '▲ ' + (no(u.latest) || 'update'));
    if (no(u.current)) {
      w.appendChild(document.createTextNode(' (have ' + no(u.current) + ')'));
    }
    cell.appendChild(w);
  }

  /* ---------------------------------------------------------- LAN rows */

  function renderLan(snap) {
    var body = $('body-lan');
    var devs = (snap.lan && Array.isArray(snap.lan.devices)) ? snap.lan.devices : [];
    body.textContent = '';

    if (!devs.length) {
      var e = el('tr', 'empty');
      var td = el('td', '', 'no LAN devices in this snapshot');
      td.colSpan = 9;
      e.appendChild(td);
      body.appendChild(e);
      $('lan-meta').textContent = '0 devices';
      return;
    }

    var counts = { online: 0, total: devs.length, edge: 0, newc: 0 };

    devs.forEach(function (d) {
      d = d || {};
      var mac = no(d.mac), ip = no(d.ip);
      var online = d.state ? d.state !== 'offline' : true;
      if (online) counts.online++;
      if (d.is_gateway || no(d.kind).toLowerCase() === 'gateway') counts.edge++;
      if (d.state === 'new') counts.newc++;

      var tr = el('tr');

      /* name + tags */
      var tdName = el('td');
      var box = el('div', 'name-cell');
      var host = no(d.hostname) || no(d.name);
      var main = el('div', 'name-main');
      var hostBtn = metric('Hostname', host || '(no hostname)');
      main.appendChild(hostBtn);
      flash(hostBtn, 'lan-host-' + (mac || ip), host || ip);
      box.appendChild(main);

      var sub = el('div', 'name-sub');
      var et = edgeTag(d.kind, d.is_gateway);
      if (et) sub.appendChild(el('span', et[0], et[1]));
      if (no(d.os_guess)) sub.appendChild(el('span', '', no(d.os_guess)));
      if (Array.isArray(d.services) && d.services.length) {
        sub.appendChild(el('span', '', d.services.length + ' svc'));
      }
      if (Array.isArray(d.sources) && d.sources.length) {
        sub.appendChild(el('span', '', d.sources.join('+')));
      }
      if (sub.childNodes.length) box.appendChild(sub);
      tdName.appendChild(box);
      tr.appendChild(tdName);

      /* ip / mac / vendor */
      var tdIp = el('td'); tdIp.appendChild(metric('IP', ip));
      flash(tdIp.firstChild, 'lan-ip-' + (mac || ip), ip);
      tr.appendChild(tdIp);

      var tdMac = el('td'); tdMac.appendChild(metric('MAC', mac));
      tr.appendChild(tdMac);

      var tdV = el('td'); tdV.appendChild(metric('Vendor', d.vendor));
      tr.appendChild(tdV);

      var tdI = el('td', 'c-hide-sm'); tdI.appendChild(metric('Iface', d.iface));
      tr.appendChild(tdI);

      var tdR = el('td', 'c-hide-sm'); tdR.appendChild(metric('RTT', ms(d.rtt_ms)));
      tr.appendChild(tdR);

      var tdS = el('td', 'c-hide-sm');
      var seen = no(d.last_seen);
      tdS.appendChild(metric('Last seen', seen ? (clockTime(seen) || ago(seen)) : ''));
      tr.appendChild(tdS);

      var tdSt = el('td');
      tdSt.appendChild(pill(d.state === 'offline' ? 'offline' : (d.state === 'new' ? 'new' : 'online'),
                            d.state || 'online'));
      tr.appendChild(tdSt);

      var tdU = el('td'); updateCell(tdU, d.update); tr.appendChild(tdU);

      /* right click = whole record */
      tr.dataset.rec = recordText('LAN device' + (host ? ' ' + host : ''), [
        ['IP', ip], ['MAC', mac], ['Hostname', host], ['Vendor', d.vendor],
        ['Kind', d.kind], ['OS', d.os_guess], ['Iface', d.iface],
        ['RTT', ms(d.rtt_ms)], ['State', d.state], ['Gateway', d.is_gateway ? 'yes' : ''],
        ['First seen', d.first_seen], ['Last seen', d.last_seen],
        ['Sources', Array.isArray(d.services) ? d.services.map(function (x) {
            return no(x.port) + '/' + no(x.name || x.proto);
          }).join(', ') : ''],
        ['Detected via', Array.isArray(d.sources) ? d.sources.join(', ') : ''],
        ['Update', d.update ? ((d.update.available ? 'AVAILABLE ' : 'current ') +
            (no(d.update.current) || '-') + ' -> ' + (no(d.update.latest) || '-') +
            (no(d.update.source) ? ' via ' + d.update.source : '')) : '']
      ]);
      tr.dataset.recLabel = (host || ip || 'device') + ' record';

      body.appendChild(tr);
    });

    $('lan-meta').textContent =
      counts.online + ' online / ' + counts.total + ' tracked' +
      (counts.newc ? ' · ' + counts.newc + ' new' : '');
  }

  /* ---------------------------------------------------------- USB rows */

  function renderUsb(snap) {
    var body = $('body-usb');
    var devs = (snap.usb && Array.isArray(snap.usb.devices)) ? snap.usb.devices : [];
    body.textContent = '';

    if (!devs.length) {
      var e = el('tr', 'empty');
      var td = el('td', '', 'no USB devices reported');
      td.colSpan = 7; e.appendChild(td); body.appendChild(e);
      $('usb-meta').textContent = '0 devices';
      return;
    }

    devs.forEach(function (d) {
      d = d || {};
      var tr = el('tr');
      var port = no(d.port);

      var tdP = el('td');
      var box = el('div', 'name-cell');
      var main = el('div', 'name-main');
      var pb = metric('USB port', port);
      main.appendChild(pb);
      flash(pb, 'usb-port-' + port, no(d.product));
      box.appendChild(main);
      var sub = el('div', 'name-sub');
      if (no(d.speed_mbps)) sub.appendChild(el('span', '', no(d.speed_mbps) + ' Mb/s'));
      if (no(d.max_power_ma)) sub.appendChild(el('span', '', no(d.max_power_ma) + ' mA'));
      if (no(d.product_firmware)) sub.appendChild(el('span', '', 'fw ' + no(d.product_firmware)));
      if (sub.childNodes.length) box.appendChild(sub);
      tdP.appendChild(box);
      tr.appendChild(tdP);

      var tdD = el('td'); tdD.appendChild(metric('Device', no(d.vendor) + ' ' + no(d.product)));
      tr.appendChild(tdD);

      var tdI = el('td');
      var ids = no(d.vendor_id) && no(d.product_id)
        ? no(d.vendor_id) + ':' + no(d.product_id) : no(d.vendor_id || d.product_id);
      tdI.appendChild(metric('USB IDs', ids));
      tr.appendChild(tdI);

      var tdC = el('td', 'c-hide-sm'); tdC.appendChild(metric('Class', d.device_class));
      tr.appendChild(tdC);

      var tdS = el('td', 'c-hide-sm'); tdS.appendChild(metric('Serial', d.serial));
      tr.appendChild(tdS);

      var tdDr = el('td');
      var dv = no(d.driver_version);
      tdDr.appendChild(metric('Driver', no(d.driver) + (dv ? ' ' + dv : '')));
      tr.appendChild(tdDr);

      var tdU = el('td'); updateCell(tdU, d.update); tr.appendChild(tdU);

      tr.dataset.rec = recordText('USB device' + (port ? ' ' + port : ''), [
        ['Port', port], ['Vendor', d.vendor], ['Product', d.product],
        ['Vendor ID', d.vendor_id], ['Product ID', d.product_id],
        ['Class', d.device_class], ['Subclass', d.subclass], ['Protocol', d.protocol],
        ['Serial', d.serial], ['Speed', no(d.speed_mbps) + ' Mb/s'],
        ['Max power', no(d.max_power_ma) + ' mA'], ['Hub', d.hub],
        ['Firmware', d.product_firmware],
        ['Driver', d.driver], ['Driver version', d.driver_version],
        ['Update', d.update ? ((d.update.available ? 'AVAILABLE ' : 'current ') +
            (no(d.update.current) || '-') + ' -> ' + (no(d.update.latest) || '-')) : '']
      ]);
      tr.dataset.recLabel = (no(d.product) || port || 'USB device') + ' record';

      body.appendChild(tr);
    });

    var hubs = (snap.usb && num(snap.usb.hubs)) || 0;
    $('usb-meta').textContent = devs.length + ' device' + (devs.length === 1 ? '' : 's') +
      (hubs ? ' · ' + hubs + ' hub' + (hubs === 1 ? '' : 's') : '');
  }

  /* ------------------------------------------------------- driver rows */

  function renderDrivers(snap) {
    var body = $('body-drv');
    var devs = (snap.drivers && Array.isArray(snap.drivers.devices)) ? snap.drivers.devices : [];
    body.textContent = '';

    if (!devs.length) {
      var e = el('tr', 'empty');
      var td = el('td', '', 'no drivers reported');
      td.colSpan = 7; e.appendChild(td); body.appendChild(e);
      $('drv-meta').textContent = '0 drivers';
      return;
    }

    devs.forEach(function (d) {
      d = d || {};
      var tr = el('tr');
      var key = no(d.device) + '|' + no(d.driver);

      var tdN = el('td');
      var box = el('div', 'name-cell');
      var main = el('div', 'name-main');
      var db = metric('Device', d.device);
      main.appendChild(db);
      flash(db, 'drv-' + key, no(d.version));
      box.appendChild(main);
      var sub = el('div', 'name-sub');
      if (no(d.signed) === 'no') sub.appendChild(el('span', 'tag tag-iot', 'UNSIGNED'));
      if (no(d.bus) === 'usb') sub.appendChild(el('span', '', 'usb'));
      if (sub.childNodes.length) box.appendChild(sub);
      tdN.appendChild(box);
      tr.appendChild(tdN);

      var tdB = el('td'); tdB.appendChild(metric('Bus', d.bus)); tr.appendChild(tdB);

      var tdD = el('td'); tdD.appendChild(metric('Driver', d.driver)); tr.appendChild(tdD);

      var tdV = el('td'); tdV.appendChild(metric('Version', d.version)); tr.appendChild(tdV);

      var tdP = el('td', 'c-hide-sm'); tdP.appendChild(metric('Provider', d.provider)); tr.appendChild(tdP);

      var tdDt = el('td', 'c-hide-sm'); tdDt.appendChild(metric('Date', d.date)); tr.appendChild(tdDt);

      var tdU = el('td'); updateCell(tdU, d.update); tr.appendChild(tdU);

      tr.dataset.rec = recordText('Driver' + (no(d.device) ? ' — ' + no(d.device) : ''), [
        ['Device', d.device], ['Bus', d.bus], ['Driver', d.driver],
        ['Version', d.version], ['Provider', d.provider], ['Date', d.date],
        ['Signed', d.signed],
        ['Update', d.update ? ((d.update.available ? 'AVAILABLE ' : 'current ') +
            (no(d.update.current) || '-') + ' -> ' + (no(d.update.latest) || '-') +
            (no(d.update.source) ? ' via ' + d.update.source : '')) : '']
      ]);
      tr.dataset.recLabel = (no(d.driver) || 'driver') + ' record';

      body.appendChild(tr);
    });

    $('drv-meta').textContent = devs.length + ' driver' + (devs.length === 1 ? '' : 's');
  }

  /* --------------------------------------------------------- system */

  function meterShell(name, value, sub, pct, tone) {
    var m = el('div', 'meter');
    var h = el('div', 'meter-h');
    h.appendChild(el('span', 'meter-n', name));
    h.appendChild(el('span', 'meter-v', value));
    m.appendChild(h);
    if (pct !== null && pct !== undefined) {
      var bar = el('div', 'bar' + (tone ? ' ' + tone : ''));
      var i = el('i');
      i.style.width = Math.max(0, Math.min(100, pct)) + '%';
      bar.appendChild(i);
      m.appendChild(bar);
    }
    if (sub) m.appendChild(meterSub(sub));
    return m;
  }

  /* The sub-line under a meter is a copyable value with its own label. */
  function meterSub(text) {
    var m = metric('Detail', text, 'meter-sub');
    m.classList.add('meter-sub');
    return m;
  }

  function renderSystem(snap) {
    var host = $('meters');
    host.textContent = '';
    var s = snap.system || {};

    /* CPU */
    var cpu = s.cpu || {};
    host.appendChild(meterShell('CPU', num(cpu.load_percent) !== null
      ? no(cpu.load_percent) + '%' : (no(cpu.cores) + ' cores'),
      no(cpu.model), num(cpu.load_percent), num(cpu.load_percent) >= 90 ? 'crit' : ''));

    /* memory */
    var mem = s.memory || {};
    var mp = num(mem.percent);
    host.appendChild(meterShell('Memory', num(mem.used) !== null
      ? bytes(mem.used) + ' / ' + bytes(mem.total) : '—',
      mp !== null ? mp + '% used' : '', mp, mp >= 90 ? 'crit' : (mp >= 75 ? 'hot' : '')));

    /* disks */
    var disks = Array.isArray(s.disks) ? s.disks : [];
    disks.slice(0, 3).forEach(function (d) {
      var p = num(d.percent);
      host.appendChild(meterShell('Disk ' + no(d.mount),
        num(d.used) !== null ? bytes(d.used) + ' / ' + bytes(d.total) : '—',
        p !== null ? p + '% used' : '', p, p >= 90 ? 'crit' : (p >= 80 ? 'hot' : '')));
    });
    if (!disks.length) {
      host.appendChild(meterShell('Disk', '—', 'not reported'));
    }

    /* throughput */
    var nw = s.network || {};
    host.appendChild(meterShell('Throughput',
      '↓' + bits(nw.rx_bps) + '  ↑' + bits(nw.tx_bps),
      (snap.interfaces && snap.interfaces[0]) ? no(snap.interfaces[0].name) : ''));

    /* host identity */
    host.appendChild(meterShell('Host', titleize(s.hostname) || '—',
      [no(s.os), no(s.kernel), no(s.arch)].filter(Boolean).join(' · ')));

    host.appendChild(meterShell('Uptime', dur(s.uptime_s) || '—',
      'scan mode: ' + no(snap.scan && snap.scan.mode)));

    $('sys-meta').textContent = no(s.hostname) || 'idle';
  }

  /* --------------------------------------------------------- tests */

  function renderTests(snap) {
    var body = $('body-tests');
    var tests = Array.isArray(snap.tests) ? snap.tests : [];
    body.textContent = '';

    if (!tests.length) {
      var e = el('tr', 'empty');
      var td = el('td', '', 'no tests reported');
      td.colSpan = 5; e.appendChild(td); body.appendChild(e);
      $('tests-meta').textContent = '0 tests';
      return;
    }

    var tally = { pass: 0, fail: 0, skip: 0 };
    tests.forEach(function (t) {
      t = t || {};
      var res = no(t.status).toLowerCase();
      if (tally[res] === undefined) tally[res] = 0;
      tally[res]++;

      var tr = el('tr');
      var tdN = el('td'); tdN.appendChild(metric('Test', t.name)); tr.appendChild(tdN);
      var tdT = el('td'); tdT.appendChild(metric('Target', t.target)); tr.appendChild(tdT);
      var tdR = el('td');
      tdR.appendChild(pill(['pass', 'fail', 'skip'].indexOf(res) >= 0 ? res : 'skip',
                            no(t.status).toUpperCase() || '—'));
      tr.appendChild(tdR);
      var tdD = el('td', 'c-hide-sm'); tdD.appendChild(metric('Duration', ms(t.duration_ms))); tr.appendChild(tdD);
      var tdX = el('td', 'c-hide-md'); tdX.appendChild(metric('Detail', t.detail)); tr.appendChild(tdX);

      tr.dataset.rec = recordText('Test — ' + no(t.name), [
        ['Test', t.name], ['Target', t.target], ['Status', t.status],
        ['Duration', ms(t.duration_ms)], ['Detail', t.detail]
      ]);
      tr.dataset.recLabel = (no(t.name) || 'test') + ' result';

      body.appendChild(tr);
    });

    $('tests-meta').textContent = tally.pass + ' pass · ' + tally.fail + ' fail · ' + tally.skip + ' skip';
  }

  /* ---------------------------------------------------------- alerts */

  function collectUpdates(snap) {
    var out = [];
    var push = function (kind, label, u) {
      if (u && u.available) {
        out.push({ kind: kind, label: label, current: no(u.current), latest: no(u.latest), source: no(u.source) });
      }
    };
    ((snap.lan && snap.lan.devices) || []).forEach(function (d) {
      d = d || {};
      push('LAN', (no(d.hostname) || no(d.ip) || no(d.mac)), d.update);
    });
    ((snap.usb && snap.usb.devices) || []).forEach(function (d) {
      d = d || {};
      push('USB', (no(d.product) || no(d.port)), d.update);
    });
    ((snap.drivers && snap.drivers.devices) || []).forEach(function (d) {
      d = d || {};
      push('Driver', (no(d.driver) || no(d.device)), d.update);
    });
    /* dedupe, drivers last — the request was explicit about ordering */
    var seen = Object.create(null);
    var lan = out.filter(function (o) { return o.kind !== 'Driver'; });
    var drv = out.filter(function (o) { return o.kind === 'Driver'; });
    return lan.concat(drv).filter(function (o) {
      var k = o.kind + '|' + o.label + '|' + o.latest;
      if (seen[k]) return false; seen[k] = 1; return true;
    });
  }

  function renderAlerts(snap, ups) {
    var box = $('alerts');
    box.textContent = '';

    var notes = [];
    var src = (snap.updates && snap.updates.sources) || [];
    if (Array.isArray(src) && src.length) {
      notes.push('update sources consulted: ' + src.join(', '));
    }
    if (Array.isArray(snap.privacy && snap.privacy.network_calls) &&
        snap.privacy.network_calls.length) {
      notes.push('service made ' + snap.privacy.network_calls.length +
                 ' outbound call(s) this cycle: ' + snap.privacy.network_calls.join(', '));
    }

    if (!ups.length && !notes.length) { box.hidden = true; return; }
    box.hidden = false;

    if (ups.length) {
      var a = el('div', 'alert alert-warn');
      a.appendChild(el('span', 'a-t', '▲'));
      var body = el('div');
      body.appendChild(el('div', '', ups.length + ' update' + (ups.length === 1 ? '' : 's') + ' available'));
      var ul = el('ul', 'alert-list');
      /* first five, then a count — keeps the panel short */
      ups.slice(0, 5).forEach(function (u) {
        ul.appendChild(el('li', '', '[' + u.kind + '] ' + u.label + '  ' +
          (u.current || '?') + ' → ' + (u.latest || '?') + (u.source ? '  (' + u.source + ')' : '')));
      });
      if (ups.length > 5) ul.appendChild(el('li', '', '…and ' + (ups.length - 5) + ' more'));
      body.appendChild(ul);
      a.appendChild(body);
      box.appendChild(a);
    }

    if (notes.length) {
      var b = el('div', 'alert alert-info');
      b.appendChild(el('span', 'a-t', 'i'));
      b.appendChild(el('div', '', notes.join(' · ')));
      box.appendChild(b);
    }
  }

  /* ---------------------------------------------------------- stats */

  function renderStats(snap, ups) {
    var devs = (snap.lan && snap.lan.devices) || [];
    var online = devs.filter(function (d) { return d && d.state && d.state !== 'offline'; }).length;
    var edge = devs.filter(function (d) {
      if (!d) return false;
      return d.is_gateway || LAN_EDGE_KINDS[no(d.kind).toLowerCase()];
    }).length;
    var usb = (snap.usb && Array.isArray(snap.usb.devices)) ? snap.usb.devices.length : 0;
    var drv = (snap.drivers && Array.isArray(snap.drivers.devices)) ? snap.drivers.devices.length : 0;

    $('s-lanOnline').textContent = online;
    $('s-lanOnlineSub').textContent = 'of ' + devs.length + ' seen';
    $('s-lanTotal').textContent = devs.length;
    $('s-lanTotalSub').textContent = no(snap.scan && snap.scan.subnet) || 'devices';
    $('s-edge').textContent = edge;
    $('s-edgeSub').textContent = no(snap.lan && snap.lan.gateway && snap.lan.gateway.ip) || 'routers & infra';
    $('s-usb').textContent = usb;
    $('s-usbSub').textContent = no(snap.usb && snap.usb.hubs) ? no(snap.usb.hubs) + ' hubs' : 'ports';
    $('s-drivers').textContent = drv;
    $('s-driversSub').textContent = 'loaded';
    $('s-updates').textContent = ups.length;
    $('s-updatesSub').textContent = ups.length ? 'pending' : 'all current';
    $('stat-updates').classList.toggle('hot', ups.length > 0);
  }

  /* ------------------------------------------------------- source pill */

  function renderSource() {
    var dot = $('src-dot'), label = $('src-label'), meta = $('src-meta');

    if (state.paused) {
      dot.dataset.state = 'paused';
      label.textContent = 'paused';
      meta.textContent = 'showing last snapshot';
      return;
    }
    if (state.demo) {
      dot.dataset.state = 'sample';
      label.textContent = 'offline sample';
      meta.textContent = 'not your network';
      return;
    }
    if (state.snapshot && state.lastOk && (Date.now() - state.lastOk) < STALE_MS) {
      dot.dataset.state = 'live';
      label.textContent = 'live';
      meta.textContent = state.endpoint.replace(/^https?:\/\//, '') +
        ' · ' + ago(state.snapshot.generated_at || new Date().toISOString());
      return;
    }
    if (state.lastErr) {
      dot.dataset.state = 'error';
      label.textContent = 'no service';
      meta.textContent = state.lastErr;
      return;
    }
    dot.dataset.state = 'idle';
    label.textContent = 'starting';
    meta.textContent = '';
  }

  /* ---------------------------------------------------------- top-level */

  function render(snap) {
    if (!snap || typeof snap !== 'object') return;
    state.snapshot = snap;
    state.seen = Object.create(null);

    var ups = collectUpdates(snap);
    renderStats(snap, ups);
    renderLan(snap);
    renderUsb(snap);
    renderDrivers(snap);
    renderSystem(snap);
    renderTests(snap);
    renderAlerts(snap, ups);

    var t = (snap.tool || {});
    $('foot-gen').textContent = 'snapshot ' + (no(snap.generated_at) || '?') +
      ' · ' + (no(t.name) || 'LANScan') + ' ' + (no(t.version) || '');
    $('foot-tool').textContent = no(snap.scan && snap.scan.mode)
      ? 'mode: ' + snap.scan.mode : 'LANScan';
    renderSource();
    storeInfo(snap);
  }

  function storeInfo(snap) {
    var bytes_ = 0;
    try { bytes_ = (window.localStorage.getItem(SNAP_KEY) || '').length; } catch (e) {}
    var age = Date.parse(snap.generated_at || '');
    var fresh = isFinite(age) && (Date.now() - age) <= MAX_AGE_MS;
    $('store-info').textContent =
      'last snapshot cached in localStorage: ' + (bytes_ ? (bytes_ / 1024).toFixed(1) + ' KB' : 'nothing yet') +
      ' · restored automatically on refresh' +
      (fresh ? '' : ' · snapshot is older than 7 days, treat with suspicion');
  }

  /* ================================================================ demo */

  function demoSnapshot() {
    var t = Date.now();
    function iso(msAgo) { return new Date(t - msAgo).toISOString(); }
    return {
      schema_version: 1,
      tool: { name: 'LANScan', version: '2.0.0-sample' },
      generated_at: iso(0),
      host: { hostname: 'sample-host' },
      scan: { mode: 'active', iface: 'eth0', subnet: '192.168.1.0/24', started_at: iso(1400), duration_s: 1.4 },
      interfaces: [{ name: 'eth0', ip: '192.168.1.10', mac: '02:00:00:00:00:10', state: 'up', rx_bps: 12400000, tx_bps: 2100000 }],
      lan: {
        devices: [
          { ip: '192.168.1.1', mac: '02:00:00:00:00:01', hostname: 'router.lan', vendor: 'Sample Networks', kind: 'gateway', is_gateway: true, iface: 'eth0', state: 'online', rtt_ms: 0.84, first_seen: iso(86400000), last_seen: iso(1200), sources: ['arp', 'ssdp'], services: [{ port: 80, proto: 'tcp', name: 'http' }] },
          { ip: '192.168.1.20', mac: '02:00:00:00:00:20', hostname: 'nas', vendor: 'Sample NAS', kind: 'nas', state: 'online', rtt_ms: 0.31, first_seen: iso(43200000), last_seen: iso(900), sources: ['arp', 'mdns'], services: [] },
          { ip: '192.168.1.44', mac: '02:00:00:00:00:44', hostname: '', vendor: 'Sample IoT Co', kind: 'camera', state: 'new', rtt_ms: 4.2, first_seen: iso(4000), last_seen: iso(4000), sources: ['arp'], services: [], update: { available: true, current: '1.4.2', latest: '1.6.0', source: 'local-manifest' } },
          { ip: '192.168.1.77', mac: '02:00:00:00:00:77', hostname: 'workstation', vendor: 'Sample Corp', state: 'offline', first_seen: iso(172800000), last_seen: iso(3600000), sources: ['arp'], services: [] }
        ],
        gateway: { ip: '192.168.1.1', mac: '02:00:00:00:00:01' }
      },
      usb: {
        hubs: 2,
        devices: [
          { port: '1-2', vendor_id: '0bda', product_id: '0129', vendor: 'Sample Semi', product: 'USB Hub', device_class: 'Hub', serial: 'HUB0129', speed_mbps: 480, max_power_ma: 100, hub: '1-0' },
          { port: '1-2.3', vendor_id: '0781', product_id: '5591', vendor: 'Sample Storage', product: 'Extreme SSD', device_class: 'Mass Storage', serial: '4C530001120611', speed_mbps: 10000, max_power_ma: 900, product_firmware: '3.20', driver: 'usb-storage', driver_version: '1.0', update: { available: true, current: '3.20', latest: '3.40', source: 'local-manifest' } }
        ]
      },
      drivers: {
        devices: [
          { device: 'Sample Gigabit Ethernet', bus: 'pci', driver: 'sample_e1000e', version: '3.20.4', provider: 'Sample Inc.', date: '2025-11-02', signed: 'yes', update: { available: true, current: '3.20.4', latest: '3.24.0', source: 'pkg:apt' } },
          { device: 'Extreme SSD', bus: 'usb', driver: 'usb-storage', version: '1.0', provider: 'Linux kernel', date: '2026-08-14', signed: 'yes', update: { available: false, current: '1.0' } }
        ]
      },
      system: {
        os: 'SampleOS 2', kernel: '6.12.0-sample', arch: 'x86_64', hostname: 'sample-host', uptime_s: 372345,
        cpu: { model: 'Sample CPU @ 3.40GHz', cores: 8, load_percent: 17 },
        memory: { total: 34359738368, used: 12884901888, percent: 37 },
        disks: [{ mount: '/', total: 494384795648, used: 128849018880, percent: 26 }],
        network: { rx_bps: 12400000, tx_bps: 2100000 }
      },
      tests: [
        { name: 'arp-sweep', target: '192.168.1.0/24', status: 'pass', duration_ms: 1400, detail: '254 probes, 4 replies' },
        { name: 'mdns-listen', target: 'udp/5353', status: 'pass', duration_ms: 1200, detail: '2 services announced' },
        { name: 'ssdp-probe', target: '239.255.255.250:1900', status: 'skip', duration_ms: 0, detail: 'no route' },
        { name: 'gateway-arp', target: '192.168.1.1', status: 'pass', duration_ms: 4, detail: '' }
      ],
      updates: { pending: 2, sources: ['local-manifest'] },
      privacy: { network_calls: [], storage: 'memory+localStorage', telemetry: false }
    };
  }

  /* ================================================================== io */

  function endpointUrl(path) {
    var base = no(state.endpoint) || DEFAULT_ENDPOINT;
    base = base.replace(/\/+$/, '');
    return base + path;
  }

  /* Some hardened/legacy profiles expose no fetch at all. Detect once: the
   * dashboard still renders cached snapshots and still accepts a dropped file,
   * it just cannot go live. Never let a missing global abort rendering. */
  var HAS_FETCH = typeof window.fetch === 'function';
  var HAS_ABORT = typeof window.AbortController === 'function';

  function fetchJson(path, timeoutMs) {
    if (!HAS_FETCH) return Promise.reject(new Error('fetch unavailable'));
    if (!HAS_ABORT) {
      return fetch(endpointUrl(path), { cache: 'no-store', mode: 'cors' })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)); });
    }
    var ctl = new AbortController();
    var to = setTimeout(function () { ctl.abort(); }, timeoutMs || 4000);
    return fetch(endpointUrl(path), {
      cache: 'no-store', mode: 'cors', signal: ctl.signal,
      headers: { 'Accept': 'application/json' }
    }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (j) {
      clearTimeout(to);
      return j;
    }, function (e) {
      clearTimeout(to);
      throw e;
    });
  }

  function poll() {
    if (state.paused || state.demo || state.inflight || state.probing) return;
    if (!HAS_FETCH) {
      state.lastErr = 'fetch unavailable in this browser';
      renderSource();
      return;
    }
    state.inflight = true;

    fetchJson('/api/snapshot', 4000).then(function (snap) {
      if (!snap || typeof snap !== 'object') throw new Error('malformed snapshot');
      state.lastOk = Date.now();
      state.lastErr = '';
      state.probing = false;
      setStore(SNAP_KEY, snap);   /* may fail silently; rendering is unaffected */
      render(snap);
    }).catch(function (e) {
      state.lastErr = e && e.name === 'AbortError' ? 'timeout' : (e && e.message ? e.message : 'failed');
      renderSource();
      maybeProbe();
    }).then(function () {
      state.inflight = false;
    });
  }

  /* If the configured endpoint is not there, try the documented alternates once
   * rather than spamming every poll. Loopback only, short timeouts. */
  function maybeProbe() {
    if (state.probing || state.paused || state.demo || !HAS_FETCH) return;
    if (!/^(https?:\/\/)?(127\.0\.0\.1|localhost|\[?::1\]?)(:\d+)?$/i.test(no(state.endpoint))) return;
    state.probing = true;

    var candidates = CANDIDATE_PORTS.filter(function (p) {
      return p !== parseInt((no(state.endpoint).match(/:(\d+)/) || [])[1], 10);
    });

    var i = 0;
    (function next() {
      if (i >= candidates.length) { state.probing = false; return; }
      var port = candidates[i++];
      var host = no(state.endpoint).replace(/:\d+$/, '') || 'http://127.0.0.1';
      if (!/^https?:\/\//i.test(host)) host = 'http://' + host;
      var url = host + ':' + port + '/api/snapshot';
      fetch(url, { cache: 'no-store', mode: 'cors' })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('bad')); })
        .then(function (snap) {
          state.endpoint = host + ':' + port;
          state.probing = false;
          state.lastOk = Date.now();
          state.lastErr = '';
          savePrefs();
          syncInputs();
          render(snap);
        })
        .catch(function () { next(); });
    })();
  }

  function tick() {
    if (state.timer) clearInterval(state.timer);
    if (state.paused || state.demo) { renderSource(); return; }
    state.timer = setInterval(poll, state.interval);
    poll();
  }

  /* ============================================================ bay bar */

  var btnRun = $('btn-run');
  var runLabel = $('run-label');
  var btnExport = $('btn-export');
  var btnReset = $('btn-reset');

  function renderBay() {
    if (state.paused) {
      btnRun.dataset.mode = 'paused';
      runLabel.textContent = 'PLAY';
      btnRun.title = 'Resume live scanning';
    } else {
      btnRun.dataset.mode = 'live';
      runLabel.textContent = 'PAUSE';
      btnRun.title = 'Pause live scanning (the list stops changing)';
    }
    btnRun.setAttribute('aria-pressed', state.paused ? 'true' : 'false');
    btnExport.disabled = !state.snapshot;
    renderSource();
  }

  function toggleRun() {
    state.paused = !state.paused;
    savePrefs();
    renderBay();
    if (!state.paused) { tick(); tip('resumed', 'ok'); }
    else { tip('paused — the list is frozen', 'ok'); }
  }

  function doExport() {
    if (!state.snapshot) { tip('nothing to export yet', 'err'); return; }
    var name = 'lanscan-' + (no(state.snapshot.generated_at).replace(/[:.]/g, '-') || 'snapshot') + '.json';
    var text;
    try { text = JSON.stringify(state.snapshot, null, 2); }
    catch (e) { tip('export failed — snapshot not serialisable', 'err'); return; }
    var blob = new Blob([text], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
    copyText(text, 'Snapshot JSON');
    tip('exported ' + name, 'ok');
  }

  function doReset() {
    if (!window.confirm('Clear the cached snapshot and start from scratch?')) return;
    dropStore(SNAP_KEY);
    dropStore(STORE_KEY);
    state.snapshot = null;
    state.seen = Object.create(null);
    state.lastOk = 0;
    state.lastErr = '';
    state.paused = false;
    state.demo = false;
    state.endpoint = DEFAULT_ENDPOINT;
    state.interval = 2000;
    syncInputs();
    savePrefs();
    $('body-lan').textContent = '';
    $('body-usb').textContent = '';
    $('body-drv').textContent = '';
    $('body-tests').textContent = '';
    $('meters').textContent = '';
    $('alerts').hidden = true;
    $('alerts').textContent = '';
    renderBay();
    tick();
    tip('reset — scanning from scratch', 'ok');
  }

  /* ============================================================ plumbing */

  function syncInputs() {
    $('in-endpoint').value = state.endpoint;
    $('in-interval').value = String(state.interval);
    $('in-demo').checked = state.demo;
  }

  function bind() {
    btnRun.addEventListener('click', toggleRun);
    btnExport.addEventListener('click', doExport);
    btnReset.addEventListener('click', doReset);

    /* left click a metric → copy that value.
     * right click a row    → copy the whole record.
     * shift+left click    → same as right click, for trackpads without a
     *                       secondary button. */
    document.addEventListener('click', function (ev) {
      var m = ev.target.closest ? ev.target.closest('.m') : null;
      if (!m || m.disabled) return;
      ev.preventDefault();
      if (ev.shiftKey) {
        var tr = m.closest('tr');
        if (tr && tr.dataset.rec) { copyText(tr.dataset.rec, tr.dataset.recLabel || 'Record'); return; }
      }
      copyText(m.dataset.val, m.dataset.label);
    });

    document.addEventListener('contextmenu', function (ev) {
      var tr = ev.target.closest ? ev.target.closest('tr') : null;
      if (!tr || !tr.dataset.rec) return;
      ev.preventDefault();
      copyText(tr.dataset.rec, tr.dataset.recLabel || 'Record');
    });

    /* keyboard parity — a metric is a button, so Enter/Space already work; add
     * the record shortcut for completeness. */
    document.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Enter' || !ev.shiftKey) return;
      var m = document.activeElement;
      if (!m || !m.classList || !m.classList.contains('m')) return;
      ev.preventDefault();
      var tr = m.closest('tr');
      if (tr && tr.dataset.rec) copyText(tr.dataset.rec, tr.dataset.recLabel || 'Record');
    });

    $('btn-apply').addEventListener('click', function () {
      var v = no($('in-endpoint').value);
      if (v && !/^https?:\/\//i.test(v)) v = 'http://' + v;
      if (v) state.endpoint = v.replace(/\/+$/, '');
      var iv = num($('in-interval').value);
      state.interval = iv && iv >= 500 ? iv : 2000;
      state.demo = !!$('in-demo').checked;
      state.lastErr = '';
      savePrefs();
      syncInputs();
      if (state.demo) { render(demoSnapshot()); tip('offline sample data — not your network'); }
      else { tick(); tip('connecting to ' + state.endpoint.replace(/^https?:\/\//, '')); }
    });

    $('in-demo').addEventListener('change', function () {
      state.demo = this.checked;
      savePrefs();
      if (state.demo) { render(demoSnapshot()); tip('offline sample data — not your network'); }
      else { tick(); }
    });

    $('btn-loadfile').addEventListener('click', function () { $('in-file').click(); });
    $('in-file').addEventListener('change', function () {
      var f = this.files && this.files[0];
      if (!f) return;
      var fr = new FileReader();
      fr.onload = function () {
        try {
          var j = JSON.parse(String(fr.result));
          if (!j || typeof j !== 'object') throw new Error('not an object');
          setStore(SNAP_KEY, j);
          render(j);
          tip('loaded ' + f.name, 'ok');
        } catch (e) {
          tip('could not parse ' + f.name, 'err');
        }
      };
      fr.onerror = function () { tip('could not read ' + f.name, 'err'); };
      fr.readAsText(f);
      this.value = '';
    });

    /* pause polling when the tab is hidden — a hidden tab has no business
     * hammering a LAN scanner. */
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { if (state.timer) { clearInterval(state.timer); state.timer = null; } }
      else if (!state.paused && !state.demo) { tick(); }
    });

    window.addEventListener('pagehide', function () { if (state.timer) clearInterval(state.timer); });
  }

  /* ================================================================= boot */

  function boot() {
    loadPrefs();
    syncInputs();
    bind();
    renderBay();

    /* 1 — restore last snapshot so a refresh never shows an empty page */
    var cached = store(SNAP_KEY);
    if (cached && typeof cached === 'object') { render(cached); tip('restored last snapshot from this browser'); }

    /* 2 — demo mode short-circuits the network entirely */
    if (state.demo) { render(demoSnapshot()); renderBay(); return; }

    /* 3 — go live */
    tick();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

})();
