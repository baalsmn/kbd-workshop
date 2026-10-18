// Molex 505278-1270 Easy-On FFC/FPC connector, 12 pins, 0.5 mm pitch,
// right angle, SMD. Converted from the official molex_5052781270_12p.kicad_mod
//
// Pads 1..12 (x=-2.75 .. +2.75, y=-2.425) -> params.P1 .. params.P12
// Pads 13, 14 = mounting tabs (x=-+5.05)   -> params.MP
// 3D model: Molex_505278-1270.step (simplified, tools/lib/make_models.py). The default path assumes the
// Ergogen output layout (output/pcbs/<board>.kicad_pcb, STEP file next to the
// config); point model at another file/folder if your project lives elsewhere.
//
// side: 'F' = front copper, 'B' = back copper (X flipped)

const params = { designator: 'J', side: 'F' }
for (let n = 1; n <= 12; n++) {
  params[`P${n}`] = {type: 'net', value: `FFC_${n}`}
}
params.MP = {type: 'net', value: 'GND'}
params.model = '${KIPRJMOD}/../../3dmodels/Molex_505278-1270.step'
params.model_offset = [0, -1.35, 0]   // aligns the model (tools/lib/make_models.py) with the pads
params.model_rotation = [0, 0, 0]

module.exports = {
  params,
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''
    const line = (x1, y1, x2, y2, layer, w) =>
      `(fp_line (start ${x(x1)} ${y1}) (end ${x(x2)} ${y2}) (stroke (width ${w}) (type solid)) (layer "${L(layer)}"))`
    const outline = (pts, layer, w) =>
      pts.slice(1).map((pt, i) => line(pts[i][0], pts[i][1], pt[0], pt[1], layer, w)).join('\n    ')
    const layers = `(layers "${L('F.Cu')}" "${L('F.Paste')}" "${L('F.Mask')}")`

    const pins = []
    for (let n = 1; n <= 12; n++) {
      const px = -2.75 + (n - 1) * 0.5
      pins.push(`(pad "${n}" smd rect (at ${x(px)} -2.425 ${p.r}) (size 0.3 1) ${layers} ${p[`P${n}`].str})`)
    }

    const body = [
      [-4.7, -2.225], [4.7, -2.225], [4.7, -2.625], [5.35, -2.625], [5.35, 1.475],
      [4.5, 1.475], [4, 2.625], [-4, 2.625], [-4.5, 1.475], [-5.35, 1.475],
      [-5.35, -2.625], [-4.7, -2.625], [-4.7, -2.225],
    ]

    return `
  (footprint "molex_505278"
    (layer "${L('F.Cu')}")
    ${p.at}
    (attr smd)

    (property "Reference" "${p.ref}"
      (at 0 -0.15 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 1.27 1.27) (thickness 0.254))${mirror})
    )

    (fp_rect (start ${x(-7.05)} -3.925) (end ${x(7.05)} 3.625)
      (stroke (width 0.1) (type solid)) (fill none) (layer "${L('F.CrtYd')}"))

    ${outline(body, 'F.Fab', 0.1)}

    ${outline([[-3.5, -2.225], [-4.7, -2.225], [-4.7, -2.625], [-5.35, -2.625], [-5.35, -0.825]], 'F.SilkS', 0.2)}
    ${outline([[3.5, -2.225], [4.7, -2.225], [4.7, -2.625], [5.35, -2.625], [5.35, -0.825]], 'F.SilkS', 0.2)}
    ${outline([[-5.35, 1.475], [-4.5, 1.475], [-4, 2.625], [4, 2.625], [4.5, 1.475], [5.35, 1.475]], 'F.SilkS', 0.2)}
    (fp_circle (center ${x(-2.75)} -3.35) (end ${x(-2.75)} -3.3)
      (stroke (width 0.1) (type solid)) (fill none) (layer "${L('F.SilkS')}"))

    ${pins.join('\n    ')}

    (pad "13" smd rect (at ${x(-5.05)} 0.275 ${p.r + 90}) (size 1.3 2) ${layers} ${p.MP.str})
    (pad "14" smd rect (at ${x(5.05)} 0.275 ${p.r + 90}) (size 1.3 2) ${layers} ${p.MP.str})

    (model "${p.model}"
      (offset (xyz ${p.model_offset[0]} ${back ? -p.model_offset[1] : p.model_offset[1]} ${p.model_offset[2]}))
      (scale (xyz 1 1 1))
      (rotate (xyz ${p.model_rotation[0]} ${p.model_rotation[1]} ${p.model_rotation[2] + (back ? 180 : 0)})))
  )
  `
  },
}
