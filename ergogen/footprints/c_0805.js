// SMD capacitor 0805 (2012 metric), IPC-7351 nominal.
// Converted from KiCad's library footprint Capacitor_SMD:C_0805_2012Metric (KiCad 10).
//
// Pad 1 (x=-0.95) -> params.from
// Pad 2 (x=+0.95) -> params.to
// value: written to the footprint's Value field (e.g. '10uF')
//
// side: 'F' = front copper, 'B' = back copper (X flipped, as when a
//       footprint is flipped to the back in KiCad)

module.exports = {
  params: {
    designator: 'C',
    lcsc: 'C15850',   // LCSC / JLCPCB part: 10uF 25V X5R 0805, Samsung CL21A106KAYNNNE (JLC basic) ('' = none)
    side: 'F',
    value: '',
    from: {type: 'net', value: 'VCC'},
    to: {type: 'net', value: 'GND'},
  },
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''
    const layers = `(layers "${L('F.Cu')}" "${L('F.Paste')}" "${L('F.Mask')}")`

    return `
  (footprint "c_0805"
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
      (at 0 -1.68 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 0.8 0.8) (thickness 0.15))${mirror})
    )
    (property "Value" "${p.value}"
      (at 0 1.68 ${p.r})
      (layer "${L('F.Fab')}")
      (effects (font (size 0.8 0.8) (thickness 0.12))${mirror})
    )

    (fp_line (start ${x(-0.261252)} -0.735) (end ${x(0.261252)} -0.735)
      (stroke (width 0.12) (type solid)) (layer "${L('F.SilkS')}"))
    (fp_line (start ${x(-0.261252)} 0.735) (end ${x(0.261252)} 0.735)
      (stroke (width 0.12) (type solid)) (layer "${L('F.SilkS')}"))
    (fp_rect (start ${x(-1.7)} -0.98) (end ${x(1.7)} 0.98)
      (stroke (width 0.05) (type solid)) (fill none) (layer "${L('F.CrtYd')}"))
    (fp_rect (start ${x(-1)} -0.625) (end ${x(1)} 0.625)
      (stroke (width 0.1) (type solid)) (fill none) (layer "${L('F.Fab')}"))

    (pad "1" smd roundrect (at ${x(-0.95)} 0 ${p.r}) (size 1 1.45) ${layers} (roundrect_rratio 0.25) ${p.from.str})
    (pad "2" smd roundrect (at ${x(0.95)} 0 ${p.r}) (size 1 1.45) ${layers} (roundrect_rratio 0.25) ${p.to.str})

    (model "\${KIPRJMOD}/../../kicad-libraries/3dmodels/C_0805_2012Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 ${back ? 180 : 0})))
  )
  `
  },
}
