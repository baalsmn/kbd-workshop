// SK6812MINI-E addressable RGB LED, reverse mount (the body sits in a PCB
// cutout, light shines through to the other side).
// Pad layout from ceoloide's led_sk6812mini-e (MIT, back / reverse-mount
// variant): pads 1.4 x 1.0 at x = +-2.7, y = +-0.7.
//   pins (OPSCO SK6812MINI-E datasheet, LCSC/JLCPCB C5149201): 1 GND, 2 DIN,
//   3 VDD, 4 DOUT. The chamfered body corner marks pin 1 (GND). Pad positions
//   checked against the datasheet's bottom view and KiCad's ReverseMount
//   footprint (pads were numbered 1 VDD 2 DOUT 3 GND 4 DIN before; same places).
// Pads start 0.2 mm outside the cutout (JLCPCB routed-edge minimum).
//
// Params are named by function: VDD, GND, DIN, DOUT.
// side: 'B' = LED on the back, light through to the front (default)
//       'F' = LED on the front, light through to the back (X flipped)
// model: SK6812MINI-E.step (tools/lib/make_models.py, datasheet dimensions). Its origin is 5.08 mm south of the body and
//        it is drawn for a front-side switch footprint, so on side B it is
//        turned over (rotate Y 180) and shifted: lens up in the cutout, legs on
//        the back copper, chamfer on the GND pad (checked in a KiCad render).

module.exports = {
  params: {
    designator: 'LED',
    lcsc: 'C5149201',   // LCSC / JLCPCB part: OPSCO SK6812MINI-E (JLC extended) ('' = none)
    side: 'B',
    VDD: {type: 'net', value: 'VCC'},
    GND: {type: 'net', value: 'GND'},
    DIN: undefined,
    DOUT: undefined,
    model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/SK6812MINI-E.step',
    model_offset: [0, 5.08, -1.75],
    model_rotation: [0, 180, 0],
  },
  body: p => {
    const front = p.side === 'F'
    const x = v => ((front ? -1 : 1) * v).toFixed(4)
    const S = front ? 'F' : 'B'
    const mirror = front ? '' : ' (justify mirror)'
    const layers = `(layers "${S}.Cu" "${S}.Paste" "${S}.Mask")`
    const pad = (n, px, py, net) =>
      `(pad "${n}" smd rect (at ${x(px)} ${py} ${p.r}) (size 1.4 1) ${layers} ${net.str})`
    const model = p.model && !front ? `(model "${p.model}"
      (offset (xyz ${p.model_offset.join(' ')})) (scale (xyz 1 1 1)) (rotate (xyz ${p.model_rotation.join(' ')})))` : ''

    return `
  (footprint "sk6812mini_e"
    (layer "${S}.Cu")
    ${p.at}
    (attr smd)

${p.lcsc ? `    (property "LCSC" "${p.lcsc}"
      (at 0 0 ${p.r})
      (layer "${S}.Fab")
      (hide yes)
      (effects (font (size 1 1) (thickness 0.15)))
    )
` : ''}    (property "Reference" "${p.ref}"
      (at 0 2.4 ${p.r})
      (layer "${S}.SilkS")
      (effects (font (size 0.8 0.8) (thickness 0.15))${mirror})
    )

    (fp_rect (start -1.8 -1.55) (end 1.8 1.55)
      (stroke (width 0.12) (type solid)) (fill none) (layer "Edge.Cuts"))

    (fp_rect (start ${x(-3.65)} -1.65) (end ${x(3.65)} 1.65)
      (stroke (width 0.05) (type solid)) (fill none) (layer "${S}.CrtYd"))
    (fp_rect (start ${x(-1.6)} -1.4) (end ${x(1.6)} 1.4)
      (stroke (width 0.1) (type solid)) (fill none) (layer "${S}.Fab"))

    ${'' /* GND corner marker, outside the GND pad */}
    (fp_line (start ${x(-3.65)} -1.9) (end ${x(-2.0)} -1.9)
      (stroke (width 0.12) (type solid)) (layer "${S}.SilkS"))

    ${pad(1, -2.7, -0.7, p.GND)}
    ${pad(2, -2.7, 0.7, p.DIN)}
    ${pad(3, 2.7, 0.7, p.VDD)}
    ${pad(4, 2.7, -0.7, p.DOUT)}
    ${model}
  )
  `
  },
}
