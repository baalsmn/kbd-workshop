// SMD resistor 0603 (1608 metric), IPC-7351 nominal.
// Converted from KiCad's library footprint Resistor_SMD:R_0603_1608Metric (KiCad 10).
//
// Pad 1 (x=-0.825) -> params.from
// Pad 2 (x=+0.825) -> params.to
// value: written to the footprint's Value field (e.g. '330')
//
// side: 'F' = front copper, 'B' = back copper (X flipped, as when a
//       footprint is flipped to the back in KiCad)

module.exports = {
  params: {
    designator: 'R',
    side: 'F',
    value: '',
    from: undefined,
    to: undefined,
  },
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''
    const layers = `(layers "${L('F.Cu')}" "${L('F.Paste')}" "${L('F.Mask')}")`

    return `
  (footprint "r_0603"
    (layer "${L('F.Cu')}")
    ${p.at}
    (attr smd)

    (property "Reference" "${p.ref}"
      (at 0 -1.43 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 0.8 0.8) (thickness 0.15))${mirror})
    )
    (property "Value" "${p.value}"
      (at 0 1.43 ${p.r})
      (layer "${L('F.Fab')}")
      (effects (font (size 0.8 0.8) (thickness 0.12))${mirror})
    )

    (fp_line (start ${x(-0.237258)} -0.5225) (end ${x(0.237258)} -0.5225)
      (stroke (width 0.12) (type solid)) (layer "${L('F.SilkS')}"))
    (fp_line (start ${x(-0.237258)} 0.5225) (end ${x(0.237258)} 0.5225)
      (stroke (width 0.12) (type solid)) (layer "${L('F.SilkS')}"))
    (fp_rect (start ${x(-1.48)} -0.73) (end ${x(1.48)} 0.73)
      (stroke (width 0.05) (type solid)) (fill none) (layer "${L('F.CrtYd')}"))
    (fp_rect (start ${x(-0.8)} -0.4125) (end ${x(0.8)} 0.4125)
      (stroke (width 0.1) (type solid)) (fill none) (layer "${L('F.Fab')}"))

    (pad "1" smd roundrect (at ${x(-0.825)} 0 ${p.r}) (size 0.8 0.95) ${layers} (roundrect_rratio 0.25) ${p.from.str})
    (pad "2" smd roundrect (at ${x(0.825)} 0 ${p.r}) (size 0.8 0.95) ${layers} (roundrect_rratio 0.25) ${p.to.str})

    (model "\${KIPRJMOD}/../../kicad-libraries/3dmodels/R_0603_1608Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 ${back ? 180 : 0})))
  )
  `
  },
}
