// SMD capacitor 0603 (1608 metric), IPC-7351 nominal.
// Converted from C_0603_1608Metric.kicad_mod
//
// Pad 1 (x=-0.775) -> params.from
// Pad 2 (x=+0.775) -> params.to
//
// side: 'F' = front copper, 'B' = back copper (X flipped, as when a
//       footprint is flipped to the back in KiCad)

module.exports = {
  params: {
    designator: 'C',
    side: 'F',
    from: {type: 'net', value: 'VCC'},
    to: {type: 'net', value: 'GND'},
  },
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''

    return `
  (footprint "c_0603"
    (layer "${L('F.Cu')}")
    ${p.at}
    (attr smd)

    (property "Reference" "${p.ref}"
      (at 0 -1.43 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 0.8 0.8) (thickness 0.15))${mirror})
    )

    (fp_line (start ${x(-0.14058)} -0.51) (end ${x(0.14058)} -0.51)
      (stroke (width 0.12) (type solid)) (layer "${L('F.SilkS')}"))
    (fp_line (start ${x(-0.14058)} 0.51) (end ${x(0.14058)} 0.51)
      (stroke (width 0.12) (type solid)) (layer "${L('F.SilkS')}"))
    (fp_rect (start ${x(-1.48)} -0.73) (end ${x(1.48)} 0.73)
      (stroke (width 0.05) (type solid)) (fill none) (layer "${L('F.CrtYd')}"))
    (fp_rect (start ${x(-0.8)} -0.4) (end ${x(0.8)} 0.4)
      (stroke (width 0.1) (type solid)) (fill none) (layer "${L('F.Fab')}"))

    (pad "1" smd roundrect (at ${x(-0.775)} 0 ${p.r}) (size 0.9 0.95)
      (layers "${L('F.Cu')}" "${L('F.Paste')}" "${L('F.Mask')}") (roundrect_rratio 0.25)
      ${p.from.str})
    (pad "2" smd roundrect (at ${x(0.775)} 0 ${p.r}) (size 0.9 0.95)
      (layers "${L('F.Cu')}" "${L('F.Paste')}" "${L('F.Mask')}") (roundrect_rratio 0.25)
      ${p.to.str})

    (model "\${KIPRJMOD}/../../kicad-libraries/3dmodels/C_0603_1608Metric.step"
      (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 ${back ? 180 : 0})))
  )
  `
  },
}
