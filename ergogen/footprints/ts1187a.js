// SMD tactile switch XKB TS-1187A (5.1 x 5.1 x 1.5 mm), e.g. as a reset button.
// Converted from KiCad's library footprint
// Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A (KiCad 10).
//
// Pads 1 (y=-1.875, both sides) -> params.from
// Pads 2 (y=+1.875, both sides) -> params.to
//
// side: 'F' = front copper, 'B' = back copper (X flipped, as when a
//       footprint is flipped to the back in KiCad)

module.exports = {
  params: {
    designator: 'SW',
    side: 'F',
    from: {type: 'net', value: 'RST'},
    to: {type: 'net', value: 'GND'},
  },
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''
    const line = (x1, y1, x2, y2, layer, w) =>
      `(fp_line (start ${x(x1)} ${y1}) (end ${x(x2)} ${y2}) (stroke (width ${w}) (type solid)) (layer "${L(layer)}"))`
    const pad = (n, px, py, net) =>
      `(pad "${n}" smd rect (at ${x(px)} ${py} ${p.r}) (size 1 0.75) (layers "${L('F.Cu')}" "${L('F.Mask')}" "${L('F.Paste')}") ${net.str})`

    return `
  (footprint "ts1187a"
    (layer "${L('F.Cu')}")
    ${p.at}
    (attr smd)

    (property "Reference" "${p.ref}"
      (at 0 -3.75 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 1 1) (thickness 0.15))${mirror})
    )
    (property "Value" "TS-1187A"
      (at 0 3.75 ${p.r})
      (layer "${L('F.Fab')}")
      (effects (font (size 1 1) (thickness 0.15))${mirror})
    )

    ${line(-2.75, -1, -2.75, 1, 'F.SilkS', 0.12)}
    ${line(2.75, -1, 2.75, 1, 'F.SilkS', 0.12)}
    ${line(-1.3, -2.75, 1.3, -2.75, 'F.SilkS', 0.12)}
    ${line(-1.3, 2.75, 1.3, 2.75, 'F.SilkS', 0.12)}
    ${line(-1.75, -2.3, -1.3, -2.75, 'F.SilkS', 0.12)}
    ${line(-1.75, 2.3, -1.3, 2.75, 'F.SilkS', 0.12)}
    ${line(1.75, -2.3, 1.3, -2.75, 'F.SilkS', 0.12)}
    ${line(1.75, 2.3, 1.3, 2.75, 'F.SilkS', 0.12)}

    ${line(-3.75, -2.8, 3.75, -2.8, 'F.CrtYd', 0.05)}
    ${line(3.75, -2.8, 3.75, 2.8, 'F.CrtYd', 0.05)}
    ${line(3.75, 2.8, -3.75, 2.8, 'F.CrtYd', 0.05)}
    ${line(-3.75, 2.8, -3.75, -2.8, 'F.CrtYd', 0.05)}

    ${line(-2.55, -2.55, 2.55, -2.55, 'F.Fab', 0.1)}
    ${line(2.55, -2.55, 2.55, 2.55, 'F.Fab', 0.1)}
    ${line(2.55, 2.55, -2.55, 2.55, 'F.Fab', 0.1)}
    ${line(-2.55, 2.55, -2.55, -2.55, 'F.Fab', 0.1)}
    (fp_circle (center 0 0) (end 1 0) (stroke (width 0.1) (type solid)) (fill no) (layer "${L('F.Fab')}"))

    ${pad(1, -3, -1.875, p.from)}
    ${pad(1, 3, -1.875, p.from)}
    ${pad(2, -3, 1.875, p.to)}
    ${pad(2, 3, 1.875, p.to)}
  )
  `
  },
}
