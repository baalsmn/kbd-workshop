// tiny VRML 2.0 writer for KiCad (1 unit = 0.1 inch = 2.54 mm; x right, y up, z up)
const U = v => (v / 2.54).toFixed(5)
exports.box = (x0, y0, z0, x1, y1, z1, col, spec = [0.2, 0.2, 0.2], shin = 0.3) => {
  const p = [[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]]
  const f = [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
  return shape(p, f, col, spec, shin)
}
const shape = exports.shape = (pts, faces, col, spec = [0.2,0.2,0.2], shin = 0.3) => `Shape {
  appearance Appearance { material Material { diffuseColor ${col.join(' ')} specularColor ${spec.join(' ')} shininess ${shin} } }
  geometry IndexedFaceSet { solid FALSE
    coord Coordinate { point [ ${pts.map(q => q.map(U).join(' ')).join(', ')} ] }
    coordIndex [ ${faces.map(f => f.join(',') + ',-1').join(' ')} ] } }`
exports.file = shapes => `#VRML V2.0 utf8\n${shapes.join('\n')}\n`
