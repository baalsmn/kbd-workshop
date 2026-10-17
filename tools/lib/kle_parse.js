// KLE parser with label positions decoded via KLE's alignment label map.
// positions: 0 TL,1 TC,2 TR,3 CL,4 C,5 CR,6 BL,7 BC,8 BR,9 FL,10 FC,11 FR
const fs = require('fs')
const labelMap = [
  [0,6,2,8,9,11,3,5,1,4,7,10],[1,7,-1,-1,9,11,4,-1,-1,-1,-1,10],[3,-1,5,-1,9,11,-1,-1,4,-1,-1,10],[4,-1,-1,-1,9,11,-1,-1,-1,-1,-1,10],
  [0,6,2,8,10,-1,3,5,1,4,7,-1],[1,7,-1,-1,10,-1,4,-1,-1,-1,-1,-1],[3,-1,5,-1,10,-1,-1,-1,4,-1,-1,-1],[4,-1,-1,-1,10,-1,-1,-1,-1,-1,-1,-1]]
const data = JSON.parse(fs.readFileSync(process.env.KLE_FILE, 'utf8'))
const keys = []; let cur = { x: 0, y: 0, w: 1, h: 1, r: 0, rx: 0, ry: 0, a: 4 }
for (const row of data) {
  if (!Array.isArray(row)) continue
  for (const item of row) {
    if (typeof item === 'object') {
      if ('r' in item) cur.r = item.r
      if ('rx' in item) { cur.rx = item.rx; cur.x = item.rx; cur.y = cur.ry }
      if ('ry' in item) { cur.ry = item.ry; cur.y = item.ry; cur.x = cur.rx }
      if ('a' in item) cur.a = item.a
      if ('x' in item) cur.x += item.x
      if ('y' in item) cur.y += item.y
      if ('w' in item) cur.w = item.w
      if ('h' in item) cur.h = item.h
      continue
    }
    const raw = item.split('\n'), pos = Array(12).fill('')
    raw.forEach((t, i) => { const p = labelMap[cur.a][i]; if (p >= 0 && t) pos[p] = t })
    keys.push({ x: cur.x + cur.w / 2, y: cur.y + cur.h / 2, w: cur.w, pos })
    cur.x += cur.w; cur.w = 1; cur.h = 1
  }
  cur.y += 1; cur.x = cur.rx
}
module.exports = keys
