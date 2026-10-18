// SMD diode, SOD-123.
// Converted from KiCad's library footprint Diode_SMD:D_SOD-123 (KiCad 10).
//
// Pad 1 (x=-1.65) = cathode -> params.to   (row, for COL2ROW)
// Pad 2 (x=+1.65) = anode   -> params.from (key side)
// Pads 0.9 x 1.2, rounded (25 %).
//
// side: 'F' = front copper, 'B' = back copper (X flipped, as when a
//       footprint is flipped to the back in KiCad). Default B.
// model:  STEP file (turned 180 deg on side B so the cathode band stays on pad 1:
//        KiCad flips back-side models over the X axis, this footprint mirrors X)
//        default: Diode_SOD-123.step next to the config, path
//        assumes the KiCad project is Ergogen's output/pcbs folder).

module.exports = {
  params: {
    designator: 'D',
    lcsc: 'C81598',   // LCSC / JLCPCB part: 1N4148W SOD-123 (JLC basic) ('' = none)
    side: 'B',
    from: undefined,
    to: undefined,
    model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/Diode_SOD-123.step',
  },
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''
    const line = (x1, y1, x2, y2, layer, w) =>
      `(fp_line (start ${x(x1)} ${y1}) (end ${x(x2)} ${y2}) (stroke (width ${w}) (type solid)) (layer "${L(layer)}"))`
    const layers = `(layers "${L('F.Cu')}" "${L('F.Paste')}" "${L('F.Mask')}")`

    return `
  (footprint "sod123"
    (layer "${L('F.Cu')}")
    ${p.at}
    (attr smd)

${p.lcsc ? `    (property "LCSC" "${p.lcsc}"
      (at 0 0 ${p.r})
      (layer "${L('F.Fab')}")
      (hide yes)
      (effects (font (size 1 1) (thickness 0.15)))
    )
` : ''}    (property "Reference" "${p.ref}"
      (at 0 -2 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 0.8 0.8) (thickness 0.15))${mirror})
    )

    ${'' /* silkscreen: bracket open towards the anode, closed side = cathode */}
    ${line(-2.36, -1, -2.36, 1, 'F.SilkS', 0.12)}
    ${line(-2.36, -1, 1.65, -1, 'F.SilkS', 0.12)}
    ${line(-2.36, 1, 1.65, 1, 'F.SilkS', 0.12)}

    (fp_rect (start ${x(-2.35)} -1.15) (end ${x(2.35)} 1.15)
      (stroke (width 0.05) (type solid)) (fill none) (layer "${L('F.CrtYd')}"))

    ${line(-1.4, -0.9, 1.4, -0.9, 'F.Fab', 0.1)}
    ${line(1.4, -0.9, 1.4, 0.9, 'F.Fab', 0.1)}
    ${line(1.4, 0.9, -1.4, 0.9, 'F.Fab', 0.1)}
    ${line(-1.4, 0.9, -1.4, -0.9, 'F.Fab', 0.1)}
    ${line(-0.75, 0, -0.35, 0, 'F.Fab', 0.1)}
    ${line(-0.35, -0.55, -0.35, 0.55, 'F.Fab', 0.1)}
    ${line(-0.35, 0, 0.25, -0.4, 'F.Fab', 0.1)}
    ${line(-0.35, 0, 0.25, 0.4, 'F.Fab', 0.1)}
    ${line(0.25, -0.4, 0.25, 0.4, 'F.Fab', 0.1)}
    ${line(0.75, 0, 0.25, 0, 'F.Fab', 0.1)}

    (pad "1" smd roundrect (at ${x(-1.65)} 0 ${p.r}) (size 0.9 1.2) ${layers} (roundrect_rratio 0.25) ${p.to.str})
    (pad "2" smd roundrect (at ${x(1.65)} 0 ${p.r}) (size 0.9 1.2) ${layers} (roundrect_rratio 0.25) ${p.from.str})

    ${p.model ? `(model "${p.model}"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 ${back ? 180 : 0})))` : ''}
  )
  `
  },
}
