// 0xCB Helios (RP2040, Pro Micro / Elite-C form factor), USB facing away
// from the PCB. Converted from Helios_ACH.kicad_mod (castellated edges)
//
// Every pad is a net param named after its pad number: P1 .. P34.
// Pad -> Helios pin (official 0xCB pinout, rev1.0, viewed from the
// component/USB side with USB at the top = this footprint at side F):
//   left column   P31 GP10 (top corner)
//                 P1 GP0, P2 GP1, P3 GND, P4 GND, P5 GP2 (SDA), P6 GP3 (SCL),
//                 P7 GP4, P8 GP5, P9 GP6, P10 GP7, P11 GP8, P12 GP9
//   right column  P30 GP11 (top corner)
//                 P13 5V, P14 GND, P15 RST, P16 3V3, P17 GP29, P18 GP28,
//                 P19 GP27, P20 GP26, P21 GP22, P22 GP20, P23 GP23, P24 GP21
//   bottom row    P25 GP12, P26 GP13, P27 GP14, P28 GP15, P29 GP16
//   inner pads    P34 GP25 = 5 V level-shifted output for RGB LEDs
//                 P32 USB D+, P33 USB D- (test pads)
//
// Geometry from 0xCB's Helios_ACH.kicad_mod (github.com/0xCB-dev/0xCB-Helios): every pin has a 1.0 mm
// through-hole plus a 3.5 x 1.8 mm castellation pad on the outer edge, so the
// Helios can be soldered flush by its castellated edges (pads 32-34 are
// through-hole only). The silkscreen leaves the castellated edges open.
//
// side: 'F' = Helios on the front, component side up.
//       'B' = Helios on the back, component side facing down (X flipped,
//             because the module is turned over).

const shapes = { 3: 'roundrect', 4: 'roundrect', 14: 'roundrect' }
const pads = [
  // [pad, x, y]
  [1, -7.62, -13.97], [2, -7.62, -11.43], [3, -7.62, -8.89], [4, -7.62, -6.35],
  [5, -7.62, -3.81], [6, -7.62, -1.27], [7, -7.62, 1.27], [8, -7.62, 3.81],
  [9, -7.62, 6.35], [10, -7.62, 8.89], [11, -7.62, 11.43], [12, -7.62, 13.97],
  [13, 7.62, -13.97], [14, 7.62, -11.43], [15, 7.62, -8.89], [16, 7.62, -6.35],
  [17, 7.62, -3.81], [18, 7.62, -1.27], [19, 7.62, 1.27], [20, 7.62, 3.81],
  [21, 7.62, 6.35], [22, 7.62, 8.89], [23, 7.62, 11.43], [24, 7.62, 13.97],
  [25, -5.08, 13.97], [26, -2.54, 13.97], [27, 0, 13.97], [28, 2.54, 13.97],
  [29, 5.08, 13.97], [30, 7.62, -16.51], [31, -7.62, -16.51],
  [32, -1.27, -8.89], [33, 1.27, -8.89], [34, -5.08, 11.43],
]

// power pins: 5V (USB VBUS) feeds the LED rail VCC
const defaults = { 3: 'GND', 4: 'GND', 14: 'GND', 13: 'VCC', 15: 'RST', 16: '3V3' }
const params = {
  designator: 'MCU',
  side: 'F',
  // 3D model: exact Helios rev1.0, exported with kicad-cli from 0xCB's own
  // KiCad design (github.com/0xCB-dev/0xCB-Helios), origin = pin grid centre.
  model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/Helios_0xCB_rev1.0.step',
  model_offset: [0, 0, 0],
}
for (const [n] of pads) {
  params[`P${n}`] = {type: 'net', value: defaults[n] || `MCU_P${n}`}
}


// castellation pads [pad, x, y, rotation]
const castellations = [
  ...[1,2,3,4,5,6,7,8,9,10,11,12].map((n, i) => [n, -8.92, -13.97 + 2.54 * i, 0]),
  ...[13,14,15,16,17,18,19,20,21,22,23,24].map((n, i) => [n, 8.92, -13.97 + 2.54 * i, 0]),
  ...[25,26,27,28,29].map((n, i) => [n, -5.08 + 2.54 * i, 15.27, 90]),
  [30, 8.92, -16.51, 0], [31, -8.92, -16.51, 0],
]

module.exports = {
  params,
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''
    const stroke = '(stroke (width 0.15) (type solid))'
    const line = (x1, y1, x2, y2) =>
      `(fp_line (start ${x(x1)} ${y1}) (end ${x(x2)} ${y2}) ${stroke} (layer "${L('F.SilkS')}"))`
    const arc = (sx, sy, mx, my, ex, ey) =>
      `(fp_arc (start ${x(sx)} ${sy}) (mid ${x(mx)} ${my}) (end ${x(ex)} ${ey}) ${stroke} (layer "${L('F.SilkS')}"))`
    const text = (t, tx, ty, layer) =>
      `(fp_text user "${t}" (at ${x(tx)} ${ty} ${p.r}) (layer "${L(layer)}") (effects (font (size 1 1) (thickness 0.15)) (justify bottom${back ? ' mirror' : ''})))`

    const tht = pads.map(([n, px, py]) => {
      const shape = shapes[n] || 'circle'
      const rr = shape === 'roundrect' ? ' (roundrect_rratio 0.25)' : ''
      return `(pad "${n}" thru_hole ${shape} (at ${x(px)} ${py} ${p.r}) (size 1.8 1.8) (drill 1) (layers "*.Cu" "*.Mask")${rr} ${p[`P${n}`].str})`
    })
    const smd = castellations.map(([n, px, py, rot]) =>
      `(pad "${n}" smd roundrect (at ${x(px)} ${py} ${p.r + rot}) (size 3.5 1.8) (layers "${L('F.Cu')}" "${L('F.Mask')}") (roundrect_rratio 0.25) ${p[`P${n}`].str})`)

    // model: on the back the module is turned over (KiCad flips back-side
    // models over the X axis, this footprint mirrors X -> extra 180 deg turn)
    const mo = p.model_offset
    const model = p.model ? `(model "${p.model}"
      (offset (xyz ${back ? -mo[0] : mo[0]} ${back ? -mo[1] : mo[1]} ${mo[2]})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 ${back ? 180 : 0})))` : ''

    return `
  (footprint "helios"
    (layer "${L('F.Cu')}")
    ${p.at}
    (attr through_hole exclude_from_pos_files exclude_from_bom)

    (property "Reference" "${p.ref}"
      (at ${x(-10.58)} 16.44 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 1 1) (thickness 0.15)) (justify ${back ? 'right mirror' : 'left'}))
    )

    ${text('1', -6.02, -13.2825, 'F.SilkS')}
    ${text('USB', 0, -16.2, 'F.SilkS')}
    ${text('topside', 0, -14.8, 'F.SilkS')}

    ${line(-6.22, 15.44, -7.62, 15.44)}
    ${line(7.62, 15.44, 6.22, 15.44)}
    ${line(-3.55, -14.2, -3.55, -17.98)}
    ${line(3.55, -14.2, -3.55, -14.2)}
    ${line(3.55, -14.2, 3.55, -17.98)}
    ${line(7.62, -17.98, -7.62, -17.98)}
    ${arc(-8.659446, -17.549446, -8.182544, -17.868102, -7.62, -17.98)}
    ${arc(-7.62, 15.44, -8.182545, 15.328103, -8.659447, 15.009447)}
    ${arc(7.62, -17.98, 8.182545, -17.868103, 8.659447, -17.549447)}
    ${arc(8.659447, 15.009447, 8.182545, 15.328103, 7.62, 15.44)}

    (fp_rect (start ${x(-4.45)} -18.63) (end ${x(4.45)} -11.98)
      ${stroke} (fill none) (layer "Cmts.User"))
    (fp_rect (start ${x(8.89)} -17.78) (end ${x(-8.89)} 15.24)
      (stroke (width 0.2) (type solid)) (fill none) (layer "Cmts.User"))

    ${tht.join('\n    ')}
    ${smd.join('\n    ')}
    ${model}
  )
  `
  },
}
