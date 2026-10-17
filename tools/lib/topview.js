// 2D top view (SVG) of a built design: case + PCB + centre cover outlines from
// out/outlines/*.dxf, keycaps from out/points/points.yaml, legends from a KLE file.
// Usage: node tools/lib/topview.js <project dir> <kle json> <out.svg>
// Legend shown: centre-left (Hungarian character), else front-centre (QMK keycode).
// Inline styles only (some SVG rasterizers ignore <style> blocks).
const fs = require('fs'), path = require('path')
const [,, P, kleFile, outFile] = process.argv
process.env.KLE_FILE = kleFile
const kle = require('./kle_parse.js')

// --- DXF (LINE / ARC / CIRCLE / LWPOLYLINE) -> SVG path data, y flipped
const BB = [1e9, 1e9, -1e9, -1e9]
const bb = (x, y) => { BB[0] = Math.min(BB[0], x); BB[1] = Math.min(BB[1], y); BB[2] = Math.max(BB[2], x); BB[3] = Math.max(BB[3], y) }
function dxfPaths(file, track) {
  const t = fs.readFileSync(file, 'utf8').split(/\r?\n/).map(s => s.trim())
  const d = []
  for (let i = 0; i < t.length - 1; i++) {
    if (t[i] !== '0') continue
    const type = t[i + 1], o = {}, pts = []
    for (let j = i + 2; j < t.length - 1 && t[j] !== '0'; j += 2) {
      if (type === 'LWPOLYLINE' && t[j] === '10') pts.push([+t[j + 1], 0])
      else if (type === 'LWPOLYLINE' && t[j] === '20') pts[pts.length - 1][1] = +t[j + 1]
      else o[t[j]] = +t[j + 1]
    }
    if (type === 'LINE') {
      if (track) { bb(o[10], -o[20]); bb(o[11], -o[21]) }
      d.push(`M${o[10]} ${-o[20]}L${o[11]} ${-o[21]}`)
    }
    if (type === 'CIRCLE') {
      const r = o[40]
      d.push(`M${o[10] - r} ${-o[20]}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0Z`)
    }
    if (type === 'ARC') {
      // DXF arcs run counter-clockwise as seen on screen too (y is flipped for display) -> sweep flag 0
      const r = o[40], a1 = o[50] * Math.PI / 180, a2 = o[51] * Math.PI / 180
      let sweep = o[51] - o[50]; if (sweep < 0) sweep += 360
      const x1 = o[10] + r * Math.cos(a1), y1 = o[20] + r * Math.sin(a1), x2 = o[10] + r * Math.cos(a2), y2 = o[20] + r * Math.sin(a2)
      if (track) { bb(x1, -y1); bb(x2, -y2) }
      d.push(`M${x1} ${-y1}A${r} ${r} 0 ${sweep > 180 ? 1 : 0} 0 ${x2} ${-y2}`)
    }
    if (type === 'LWPOLYLINE' && pts.length) d.push('M' + pts.map(p => `${p[0]} ${-p[1]}`).join('L') + (o[70] & 1 ? 'Z' : ''))
  }
  return d.join('')
}

// --- key points (x, y, rotation, keycap width)
const K = {}; let cur = null
for (const l of fs.readFileSync(path.join(P, 'out/points/points.yaml'), 'utf8').split('\n')) {
  let m = /^((?:mirror_)?[\w-]+_c\d+_r\d+):/.exec(l); if (m) { cur = m[1]; K[cur] = { u: 1 }; continue }
  if (/^\S/.test(l)) cur = null; if (!cur) continue
  m = /^    (x|'y'|r): ([-\d.e]+)/.exec(l); if (m) K[cur][m[1].replace(/'/g, '')] = +m[2]
  m = /^        keycap_u: ([\d.]+)/.exec(l); if (m) K[cur].u = +m[1]
}
const names = Object.keys(K)
const o = K[names.find(n => /^[\w-]+_c1_r1$/.test(n) && !n.startsWith('mirror_'))]
const a = 15 * Math.PI / 180
// KLE key of c1_r1 = bottom-left key; left key -> KLE (c1.x + local x, c1.y - local y);
// right half = mirror of the left in the KLE file (x -> 21.5 - x)
const c1 = kle.filter(k => k.x < 4).reduce((m, k) => (k.y > m.y + 1e-6 || (Math.abs(k.y - m.y) < 1e-6 && k.x < m.x)) ? k : m)
const legend = (lx, ly, mirror) => {
  const tx0 = c1.x + lx, ty = c1.y - ly, tx = mirror ? 21.5 - tx0 : tx0
  const k = kle.reduce((b, q) => { const dd = Math.hypot(q.x - tx, q.y - ty); return dd < b.d ? { d: dd, q } : b }, { d: 1e9 })
  if (!k.q || k.d > 0.2) return '?'
  const p = k.q.pos; return (p[3] || p[10] || p[4] || p[0] || '').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
}
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
let caps = ''
for (const n of names) {
  const k = K[n], mirror = n.startsWith('mirror_')
  const src = mirror ? K[n.replace('mirror_', '')] : k
  const dx = src.x - o.x, dy = src.y - o.y
  const lx = (dx * Math.cos(a) - dy * Math.sin(a)) / 19, ly = (dx * Math.sin(a) + dy * Math.cos(a)) / 19
  const w = (k.u - 1) * 19 + 18.2, h = 18.2
  const txt = esc(legend(lx, ly, mirror))
  caps += `<g transform="translate(${k.x} ${-k.y}) rotate(${-k.r})">` +
    `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="1.6" fill="#cfcfcf" stroke="#8a8a8a" stroke-width="0.35"/>` +
    `<text y="1.4" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="${txt.length > 4 ? 2.8 : 4}" fill="#333">${txt}</text></g>\n`
}

const O = f => path.join(P, 'out/outlines', f + '.dxf')
const ST = {
  case: 'fill="none" stroke="#2b2c2f" stroke-width="0.8"',
  pcb: 'fill="none" stroke="#3c9a3c" stroke-width="0.4" stroke-dasharray="2 1.2"',
  cover: 'fill="none" stroke="#666" stroke-width="0.5"',
  tp: 'fill="#1a1a1a" stroke="#000" stroke-width="0.3"',
  ind: 'fill="#ffd24a" stroke="#a07800" stroke-width="0.3"',
  hid: 'fill="none" stroke="#e0503c" stroke-width="0.35" stroke-dasharray="0.8 0.5"',  // hidden: under the pad / in the floor
}
const layers = [['case', 'case'], ['pcb', 'pcb'], ['center_cover_top', 'cover'], ['center_cover_ring', 'cover'], ['cirque_flush', 'tp'], ['indicator_holes', 'ind'],
  ['trackpad_riser_cols', 'hid'], ['tp_clip_lip', 'hid'], ['tp_key', 'hid'], ['mcu_reset_boss', 'hid']]
const body = layers.map(([f, c]) => fs.existsSync(O(f)) ? `<path d="${dxfPaths(O(f), c === 'case')}" ${ST[c]}/>` : '').join('\n')
const pad = 6, x0 = BB[0] - pad, y0 = BB[1] - pad, W = BB[2] - BB[0] + 2 * pad, H = BB[3] - BB[1] + 2 * pad

fs.writeFileSync(outFile, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${x0} ${y0} ${W} ${H}" width="${Math.round(W * 4)}" height="${Math.round(H * 4)}">
<rect x="${x0}" y="${y0}" width="${W}" height="${H}" fill="#f4f4f6"/>
${body}
${caps}</svg>
`)
console.log('wrote', outFile)
