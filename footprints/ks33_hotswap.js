// Gateron KS-33 hotswap socket (KS-2P02B01-02), 1U or wider (2U with stabilizer).
// Converted from Gateron-KS33-Hotswap-1U.kicad_mod.
//
// Geometry is TOP VIEW (as KiCad shows the board), checked against the
// Gateron STEP models: the KS-33 switch has its pins at (+2.6, 5.75) and
// (-4.4, 4.70), and the socket's contact cups land on exactly those spots.
// Gateron's "PCB Layout" drawings (switch and socket PDFs) are drawn as seen
// from below, i.e. mirrored in X compared with this.
//   centre hole 5.25 (switch drawing), switch pin holes 3.0
//
// Pads from the KS-2P02B01-02 socket drawing (measured from its vector data),
// in top view; the socket terminals end at x = -8.39 and +6.59 (STEP model):
// Pad 1 (x=-8.2,  y=4.7,  2.45 x 2.55) -> params.from
// Pad 2 (x=+6.35, y=5.75, 2.45 x 2.55) -> params.to
//
// side: 'B' = socket on the back (default, the real use).
//       'F' = everything mirrored to the front (only for completeness).
// Coordinates are hard-coded, so mirrored points get the SAME pad layout
// (only the key rotation differs).
//
// width: keycap width in U, only widens the keycap outline (Dwgs.User).
// stab:  true adds PCB clearance cutouts for a Gateron KS-57 low-profile
//        plate-mounted 2U stabilizer (housings at x = +-12, from the KS-57B210T
//        drawing; the housing reaches ~3.2 mm below the plate, deeper than the
//        plate-to-PCB gap). Pad 1 is trimmed to stay 0.5 mm off the cutout.
//        The matching plate cutout is an Ergogen outline (stab_cutouts).

module.exports = {
  params: {
    designator: 'S',
    side: 'B',
    width: 1,
    stab: false,
    from: undefined,
    to: undefined,
    // 3D models (STEP files next to the config; default paths assume the
    // KiCad project is Ergogen's output/pcbs folder). '' = no model.
    // The Gateron switch and stabilizer models share one origin (key centre at
    // x = 60, PCB top at z = 3.25), so both get the same transform: turned over
    // (rotate X 180, because the footprint is on the back) and shifted onto
    // the board (offset -60, 0, 3.25 - 1.6). The stabilizer model is only
    // added on keys with stab: true.
    socket_model: '${KIPRJMOD}/../../3dmodels/Gateron_ks33_hotswap_socket.step',
    switch_model: '${KIPRJMOD}/../../3dmodels/KS-33 Low Profile 2.0  KS33-20230109（KS-33-Y31  3D图）.stp',
    stab_model: '${KIPRJMOD}/../../3dmodels/low profile stabilizer..stp',
    // low-profile keycap (VRML, generated), file chosen by width: {w} is
    // replaced with 1, 1.25 or 2 (keycap_lowprofile_1u/1.25u/2u.wrl); '' = none
    keycap_model: '${KIPRJMOD}/../../3dmodels/keycap_lowprofile_{w}u.wrl',
    socket_model_offset: [0, 0, 0],
    socket_model_rotation: [0, 0, 0],
    switch_model_offset: [-60, 0, 1.65],
    switch_model_rotation: [180, 0, 0],
  },
  body: p => {
    const L = p.side === 'F' ? 'F' : 'B'
    const m = p.side === 'F' ? -1 : 1
    const x = v => (m * v).toFixed(4)
    const half = 9.525 * p.width

    // stabilizer housing clearance. Measured on the Gateron low-profile
    // stabilizer STEP model: below the PCB top surface each housing spans
    // x = cx-2.93 .. cx+2.93 and y = -5.03 .. +8.70 (lever end to the south).
    // Cutout = that + ~0.17-0.25 mm clearance.
    const stab_cut = cx => {
      const pts = [
        [cx - 3.1, -5.8], [cx + 3.1, -5.8], [cx + 3.1, 8.95], [cx - 3.1, 8.95],
      ]
      return `(fp_poly (pts ${pts.map(([a, b]) => `(xy ${a} ${b})`).join(' ')})
      (stroke (width 0.1) (type solid)) (fill none) (layer "Edge.Cuts"))`
    }

    const model = (file, off, rot) => file ? `(model "${file}"
      (offset (xyz ${off.join(' ')})) (scale (xyz 1 1 1)) (rotate (xyz ${rot.join(' ')})))` : ''

    // pad 1 spans x = -9.425 .. -6.975; next to a stabilizer cutout its outer
    // edge stops at -8.4 (the socket terminal itself ends at -8.39)
    const p1_outer = p.stab ? 8.4 : 8.2 + 1.225
    const p1_inner = 8.2 - 1.225
    const p1_w = p1_outer - p1_inner
    const p1_x = -(p1_outer + p1_inner) / 2

    return `
  (footprint "ks33_hotswap"
    (layer "${L}.Cu")
    ${p.at}

    (property "Reference" "${p.ref}"
      (at 0 3.5 ${p.r})
      (layer "F.SilkS")
      (effects (font (size 0.8 0.8) (thickness 0.15)))
    )

    (fp_rect (start -7 -7) (end 7 7)
      (stroke (width 0.15) (type solid)) (fill none) (layer "Dwgs.User"))
    (fp_rect (start ${-half} -9.525) (end ${half} 9.525)
      (stroke (width 0.15) (type solid)) (fill none) (layer "Dwgs.User"))

    (pad "" np_thru_hole circle (at 0 0 ${p.r}) (size 5.25 5.25) (drill 5.25) (layers "F&B.Cu" "*.Mask"))
    (pad "" np_thru_hole circle (at ${x(2.6)} 5.75 ${p.r}) (size 3 3) (drill 3) (layers "F&B.Cu" "*.Mask"))
    (pad "" np_thru_hole circle (at ${x(-4.4)} 4.7 ${p.r}) (size 3 3) (drill 3) (layers "F&B.Cu" "*.Mask"))

    (pad "1" smd roundrect (at ${x(p1_x)} 4.7 ${p.r}) (size ${p1_w.toFixed(4)} 2.55)
      (layers "${L}.Cu" "${L}.Paste" "${L}.Mask") (roundrect_rratio 0.07843137255)
      ${p.from.str})
    (pad "2" smd roundrect (at ${x(6.35)} 5.75 ${p.r}) (size 2.45 2.55)
      (layers "${L}.Cu" "${L}.Paste" "${L}.Mask") (roundrect_rratio 0.07843137255)
      ${p.to.str})
    ${p.stab ? stab_cut(-12) + '\n    ' + stab_cut(12) : ''}
    ${model(p.socket_model, p.socket_model_offset, p.socket_model_rotation)}
    ${model(p.switch_model, p.switch_model_offset, p.switch_model_rotation)}
    ${p.stab ? model(p.stab_model, p.switch_model_offset, p.switch_model_rotation) : ''}
    ${model(p.keycap_model && p.keycap_model.replace('{w}', String(+p.width)), L === 'B' ? [0, 0, -1.6] : [0, 0, 0], L === 'B' ? [180, 0, 0] : [0, 0, 0])}
  )
  `
  },
}
