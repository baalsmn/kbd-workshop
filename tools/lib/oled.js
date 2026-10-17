// 0.96" SSD1306 I2C module (27.4 x 27.2 mm), model frame = footprint frame:
// origin at the header pin row, module body towards -y (south in footprint
// coordinates), z = 0 at the keyboard PCB top. Soldered on bare header pins,
// module PCB 1.2 mm above the keyboard PCB (inside the plate cutout).
const v = require('./vrml.js')
const blue = [0.05, 0.22, 0.55], black = [0.02, 0.02, 0.03], glass = [0.06, 0.07, 0.09],
      gold = [0.85, 0.68, 0.25], plastic = [0.08, 0.08, 0.08], active = [0.01, 0.02, 0.05]
const s = []
const zb = 1.2, zt = zb + 1.2                     // module PCB bottom / top
s.push(v.box(-13.716, -25.781, zb, 13.716, 1.397, zt, blue))
// display glass (26.7 x 19.3) on the component side, between the header and the far edge
s.push(v.box(-13.35, -22.6, zt, 13.35, -3.3, zt + 1.45, glass, [0.6, 0.6, 0.6], 0.8))
// active area 21.7 x 10.9, slightly above the glass top so it reads as the "screen"
s.push(v.box(-10.87, -18.3, zt + 1.451, 10.87, -7.4, zt + 1.46, active, [0.9, 0.9, 0.9], 0.9))
// header: bare pins only (plastic spacer removed)
for (const px of [-3.81, -1.27, 1.27, 3.81]) s.push(v.box(px - 0.32, -0.32, -3.0, px + 0.32, 0.32, zt + 0.8, gold, [0.9, 0.8, 0.4], 0.6))
process.stdout.write(v.file(s))
