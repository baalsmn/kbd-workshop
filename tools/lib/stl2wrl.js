// STL (ASCII or binary) -> VRML 2.0 for KiCad (mm -> 0.1 inch units), one colour per file.
// Usage: node stl2wrl.js <in.stl> <out.wrl> <r> <g> <b> [dx dy dz [sx]]
//   dx dy dz: move the mesh (mm) before writing; sx: scale x about x = 0 after the
//   move (e.g. 1.25 to make a 1.25U keycap from a 1U one).
const fs = require('fs'), v = require('./vrml.js')
const [,, inp, out, r, g, b, dx = 0, dy = 0, dz = 0, sx = 1] = process.argv
const buf = fs.readFileSync(inp), idx = new Map(), pts = [], faces = []
const key = p => p.map(x => (+x).toFixed(4)).join(' ')
const place = p => [(p[0] + +dx) * +sx, p[1] + +dy, p[2] + +dz]
const add = tri => {
  const f = []
  for (const q of tri) { const p = place(q), k = key(p)
    if (!idx.has(k)) { idx.set(k, pts.length); pts.push(p) } f.push(idx.get(k)) }
  faces.push(f)
}
// binary: 80-byte header, triangle count, 50 bytes per triangle (normal, 3 vertices, attribute)
const n = buf.length >= 84 ? buf.readUInt32LE(80) : -1
if (n >= 0 && buf.length === 84 + n * 50) {
  for (let i = 0; i < n; i++) {
    const o = 84 + i * 50 + 12
    add([0, 1, 2].map(j => [0, 1, 2].map(k => buf.readFloatLE(o + j * 12 + k * 4))))
  }
} else {
  const txt = buf.toString('utf8')
  for (const m of txt.matchAll(/outer loop\s+vertex\s+(\S+)\s+(\S+)\s+(\S+)\s+vertex\s+(\S+)\s+(\S+)\s+(\S+)\s+vertex\s+(\S+)\s+(\S+)\s+(\S+)/g))
    add([0, 1, 2].map(i => [m[1 + 3 * i], m[2 + 3 * i], m[3 + 3 * i]].map(Number)))
}
fs.writeFileSync(out, v.file([v.shape(pts, faces, [+r, +g, +b], [0.15, 0.15, 0.15], 0.2)]))
console.log(inp.split(/[\/]/).pop(), '->', faces.length, 'triangles,', pts.length, 'points')
