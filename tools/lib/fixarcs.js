// straighten tiny arcs (chord < 1 mm) in OpenJSCAD v1 Path2D chains: the v1 arc
// code can pick the wrong (major) arc for these and add a stray near-full circle.
const fs = require('fs'); const [,, inp, out] = process.argv
let c = fs.readFileSync(inp, 'utf8'), n = 0
c = c.replace(/new CSG\.Path2D\(\[\[([-\d.e]+),([-\d.e]+)\](?:,\[([-\d.e]+),([-\d.e]+)\])*\]\)((?:\.append(?:Arc|Point)\([^)]*\))*)/g, (m) => {
  // last point of the initial array
  const init = m.slice(0, m.indexOf('])') + 2), chain = m.slice(init.length)
  const pts = [...init.matchAll(/\[([-\d.e]+),([-\d.e]+)\]/g)]; let last = pts[pts.length - 1].slice(1).map(Number)
  const fixed = chain.replace(/\.append(Arc|Point)\(\[([-\d.e]+),([-\d.e]+)\](,\{[^}]*\})?\)/g, (mm, kind, x, y) => {
    const p = [+x, +y], chord = Math.hypot(p[0] - last[0], p[1] - last[1]); last = p
    if (kind === 'Arc' && chord < 1) { n++; return `.appendPoint([${x},${y}])` }
    return mm })
  return init + fixed })
fs.writeFileSync(out, c); console.log(inp.split(/[\/]/).pop(), 'tiny arcs straightened:', n)
