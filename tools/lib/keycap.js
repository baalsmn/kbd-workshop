// Low-profile keycap (VRML), centred on the switch, z = 0 at the keyboard PCB top.
// Usage: node keycap.js <width_in_U>
const v = require('./vrml.js')
const u = +process.argv[2] || 1
const zb = 9.0, zt = 12.5                    // skirt bottom / top surface (above PCB top; top = plate top + 10)
const bw = 19.05 * u - 1.45, bh = 17.6        // base
const tw = bw - 2.2, th = bh - 2.2            // top (tapered skirt)
const cap = [0.86, 0.86, 0.84], dish = [0.80, 0.80, 0.78]
const ring = (w, h, z) => [[-w/2,-h/2,z],[w/2,-h/2,z],[w/2,h/2,z],[-w/2,h/2,z]]
const pts = [...ring(bw, bh, zb), ...ring(tw, th, zt)]
// sides + top + bottom of the frustum
const faces = [[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7],[4,5,6,7],[0,3,2,1]]
const s = [v.shape(pts, faces, cap, [0.25,0.25,0.25], 0.25)]
// shallow dish: a slightly smaller, slightly lower plate on top
const dw = tw - 1.6, dh = th - 1.6, dz = zt - 0.25
const dp = [...ring(dw, dh, dz), ...ring(dw - 0.8, dh - 0.8, dz - 0.2)]
s.push(v.shape([...ring(tw - 0.4, th - 0.4, zt + 0.001), ...ring(dw, dh, zt + 0.001)], [[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]], cap))
s.push(v.box(-dw/2, -dh/2, zt - 0.2, dw/2, dh/2, zt + 0.002, dish, [0.3,0.3,0.3], 0.35))
process.stdout.write(v.file(s))
