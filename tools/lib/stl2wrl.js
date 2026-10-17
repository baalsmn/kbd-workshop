// ASCII STL -> VRML 2.0 for KiCad (mm -> 0.1 inch units), one colour per file.
const fs = require('fs'), v = require('./vrml.js')
const [,, inp, out, r, g, b] = process.argv
const txt = fs.readFileSync(inp, 'utf8'), idx = new Map(), pts = [], faces = []
const key = p => p.map(x => (+x).toFixed(4)).join(' ')
for (const m of txt.matchAll(/outer loop\s+vertex\s+(\S+)\s+(\S+)\s+(\S+)\s+vertex\s+(\S+)\s+(\S+)\s+(\S+)\s+vertex\s+(\S+)\s+(\S+)\s+(\S+)/g)) {
  const f = []
  for (let i = 0; i < 3; i++) { const p = [m[1 + 3 * i], m[2 + 3 * i], m[3 + 3 * i]].map(Number), k = key(p)
    if (!idx.has(k)) { idx.set(k, pts.length); pts.push(p) } f.push(idx.get(k)) }
  faces.push(f)
}
fs.writeFileSync(out, v.file([v.shape(pts, faces, [+r, +g, +b], [0.15, 0.15, 0.15], 0.2)]))
console.log(inp.split(/[\/]/).pop(), '->', faces.length, 'triangles,', pts.length, 'points')
