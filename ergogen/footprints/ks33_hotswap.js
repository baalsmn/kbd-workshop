// Gateron KS-33 switch on a KS-2P02B01-02 hot-swap socket, 1U or wider (2U with
// a KS-57 stabilizer). Drawn from the Gateron datasheets (datasheets/LINKS.md):
//   KS-33E10B055NN-Y24 "PCB Layout": centre hole 5.25 (we use 5.15: 5.25 was loose), pin holes 3.00 at
//     (2.60, 5.75) and (4.40, 4.70) from the centre;
//   KS-2P02B01-02 "PCB Layout": the same two 3.0 holes 7.00 apart, pads 2.55 tall
//     on the hole rows, outer pad edges 9.40 / 7.61 from the centre (scaled from
//     the drawing's 14 mm reference: pad widths 2.45, centres 8.2 / 6.35).
//
// Geometry is TOP VIEW (as KiCad shows the board): the switch pins at (+2.6, 5.75)
// and (-4.4, 4.70); Gateron's PCB layout drawings are drawn as seen from below,
// i.e. mirrored in X compared with this. Socket terminals reach x = -8.44 / +6.65
// (15.1 tip to tip, body 11.85 from 2.42 left of the left hole).
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
//        plate-mounted 2U stabilizer (KS-57B210T drawing: housings 6.00 wide at
//        x = +-12 (24.00 apart), 4.45 below the plate top = 3.25 below a 1.2 mm
//        plate, deeper than the plate-to-PCB gap). Pad 1 is trimmed to stay
//        0.5 mm off the cutout.
//        The matching plate cutout is an Ergogen outline (stab_cutouts).

module.exports = {
  params: {
    designator: 'S',
    lcsc: 'C18212911',   // LCSC / JLCPCB part: Gateron KS-2P02B01-02 hot-swap socket (JLC extended, pre-order) ('' = none)
    side: 'B',
    width: 1,
    stab: false,
    from: undefined,
    to: undefined,
    // 3D models: Gateron's own STEP models (vendor_*, kept out of git; checked
    // against the drawings). The simplified datasheet models of
    // tools/lib/make_models.py (Gateron_KS-*.step, same frames except the
    // switch) can be used instead. Default paths assume the KiCad project is
    // Ergogen's output/pcbs folder. '' = no model.
    // Every model is turned over (rotate X 180: the footprint is on the back)
    // and shifted onto the board:
    //   socket: drawn in this footprint's frame (no transform);
    //   switch: key centre at the origin, PCB top at z = 0 -> offset (0, 0, -1.6);
    //   stabilizer: key centre at x = 60, PCB top at z = 3.25
    //     -> offset (-60, 0, 3.25 - 1.6). Only on keys with stab: true.
    socket_model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/vendor_Gateron_KS-2P02B01-02_socket.step',
    switch_model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/vendor_Gateron_KS-33_switch.step',
    stab_model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/vendor_Gateron_KS-57B210T_stabilizer.step',
    // keycap (VRML), file chosen by width: {w} is replaced with 1, 1.25 or 2. The MBK
    // caps (vendor_keycap_MBK_{w}u.wrl, from the user's MBK keycap STLs (not kept) by tools/lib/stl2wrl.js:
    // stem bottom 6.3 / rim 9.6 above the PCB top; 1.25u = the 1u cap stretched in x);
    // the generated keycap_lowprofile_{w}u.wrl (tools/lib/keycap.js) also fit. '' = none
    keycap_model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/vendor_keycap_MBK_{w}u.wrl',
    socket_model_offset: [0, 0, 0],
    socket_model_rotation: [0, 0, 0],
    switch_model_offset: [0, 0, -1.6],
    switch_model_rotation: [180, 0, 0],
    stab_model_offset: [-60, 0, 1.65],
    stab_model_rotation: [180, 0, 0],
  },
  body: p => {
    const L = p.side === 'F' ? 'F' : 'B'
    const m = p.side === 'F' ? -1 : 1
    const x = v => (m * v).toFixed(4)
    const half = 9.525 * p.width

    // stabilizer housing clearance (KS-57B210T drawing): the housing is 6.00
    // wide, 5.85 below the plate; below the plate it is 12.40 long, plus the
    // equalizing lever's end to the south (section A-A). Gateron's STEP model:
    // the part below the PCB top spans y = -5.11 .. +9.70 (5.85 x 14.81).
    // Cutout = 6.2 wide, y = -5.2 .. +9.8 (0.1 clearance at both ends).
    const stab_cut = cx => {
      const pts = [
        [cx - 3.1, -5.2], [cx + 3.1, -5.2], [cx + 3.1, 9.8], [cx - 3.1, 9.8],
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
    (attr smd)

${p.lcsc ? `    (property "LCSC" "${p.lcsc}"
      (at 0 0 ${p.r})
      (layer "${L}.Fab")
      (hide yes)
      (effects (font (size 1 1) (thickness 0.15)))
    )
` : ''}    (property "Reference" "${p.ref}"
      (at 0 3.5 ${p.r})
      (layer "F.SilkS")
      (effects (font (size 0.8 0.8) (thickness 0.15)))
    )

    ${'' /* socket body outline on the silkscreen: the stepped KS-2P02B01-02 body
      (11.85 x 5.40, r0.15 corners), from the courtyard of Gateron's KS33 hot-swap
      footprint, mirrored to this back-side frame; the terminal tabs are left out
      (they lie on the pads). Clear of the centre and pin holes. */}
    ${(() => {
      const e = `(stroke (width 0.12) (type solid)) (layer "${L}.SilkS")`
      const X = v => x(-v)       // Gateron's footprint is drawn from the socket side
      const pt = ([a, b]) => `${X(a)} ${b}`
      const line = (a, b) => `(fp_line (start ${pt(a)}) (end ${pt(b)}) ${e})`
      const arc = (a, mid, b) => `(fp_arc (start ${pt(a)}) (mid ${pt(mid)}) (end ${pt(b)}) ${e})`
      return [
        arc([-5.025, 3.525], [-4.981066, 3.418934], [-4.875, 3.375]),
        line([-4.875, 3.375], [1.184808, 3.375]),
        arc([1.184808, 3.375], [1.443627, 3.340926], [1.684808, 3.241025]),
        line([1.684808, 3.241025], [2.692949, 2.658975]),
        arc([2.692949, 2.658975], [2.93413, 2.559074], [3.192949, 2.525]),
        line([3.192949, 2.525], [6.675, 2.525]),
        arc([6.675, 2.525], [6.781066, 2.568934], [6.825, 2.675]),
        line([6.825, 2.675], [6.825, 6.725]),
        arc([6.825, 6.725], [6.781066, 6.831066], [6.675, 6.875]),
        line([6.675, 6.875], [3.492949, 6.875]),
        arc([3.492949, 6.875], [3.23413, 6.909074], [2.992949, 7.008975]),
        line([2.992949, 7.008975], [1.638397, 7.791025]),
        arc([1.638397, 7.791025], [1.397216, 7.890926], [1.138397, 7.925]),
        line([1.138397, 7.925], [0.975, 7.925]), line([0.975, 7.925], [0.975, 7.725]),
        line([0.975, 7.725], [-0.525, 7.725]), line([-0.525, 7.725], [-0.525, 7.925]),
        line([-0.525, 7.925], [-4.875, 7.925]),
        arc([-4.875, 7.925], [-4.981066, 7.881066], [-5.025, 7.775]),
        line([-5.025, 7.775], [-5.025, 3.525]),
      ].join('\n    ')
    })()}
    ${'' /* switch body (14 x 14 below the plate): corner marks only, 2 mm legs */}
    ${[[-7, -7, 1, 1], [7, -7, -1, 1], [7, 7, -1, -1], [-7, 7, 1, -1]].map(([cx, cy, dx, dy]) =>
      `(fp_line (start ${cx + 2 * dx} ${cy}) (end ${cx} ${cy}) (stroke (width 0.15) (type solid)) (layer "Dwgs.User"))
    (fp_line (start ${cx} ${cy}) (end ${cx} ${cy + 2 * dy}) (stroke (width 0.15) (type solid)) (layer "Dwgs.User"))`).join('\n    ')}
    (fp_rect (start ${-half} -9.525) (end ${half} 9.525)
      (stroke (width 0.15) (type solid)) (fill none) (layer "Dwgs.User"))

    (pad "" np_thru_hole circle (at 0 0 ${p.r}) (size 5.15 5.15) (drill 5.15) (layers "F&B.Cu" "*.Mask"))
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
    ${p.stab ? model(p.stab_model, p.stab_model_offset, p.stab_model_rotation) : ''}
    ${model(p.keycap_model && p.keycap_model.replace('{w}', String(+p.width)), L === 'B' ? [0, 0, -1.6] : [0, 0, 0], L === 'B' ? [180, 0, 0] : [0, 0, 0])}
  )
  `
  },
}
