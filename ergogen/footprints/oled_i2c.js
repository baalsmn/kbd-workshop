// 0.96" OLED 128x64, SSD1306, I2C module (4-pin header + 4 mounting holes).
// These generic modules have no vendor datasheet; the layout is the common
// module geometry: 4-pin 2.54 mm header (standard 1.7 mm pads, 1.0 mm drills)
// and the module's 4 corner holes, outline 27.4 x 27.2 mm (all measured on the
// module).
//
// Pad 1 (x=-3.81) -> params.GND
// Pad 2 (x=-1.27) -> params.VDD
// Pad 3 (x=+1.27) -> params.SCL
// Pad 4 (x=+3.81) -> params.SDA
// Excluded from the BOM and position files: the module is mounted by hand on
// header pins, not assembled by JLCPCB.
// Origin = header pin row. The module body extends ~26 mm towards +y.
//
// side: 'F' = silkscreen on front, 'B' = on back (X flipped). Pin holes
//       are through-hole either way.
// holes: false leaves out the module's 4 corner mounting holes (e.g. when
//        the module is held by its header and something sits underneath).
// VDD defaults to 3V3: the module's I2C pull-ups go to VDD, so 3.3 V keeps
// the bus safe for the RP2040 and a shared Cirque trackpad.

module.exports = {
  params: {
    designator: 'DISP',
    side: 'F',
    GND: {type: 'net', value: 'GND'},
    VDD: {type: 'net', value: '3V3'},
    holes: true,
    // 3D model (VRML): module on bare pins 1.2 mm above the PCB, display up
    model: '${KIPRJMOD}/../../kicad-libraries/3dmodels/OLED_0.96in_SSD1306_I2C_module.wrl',
    SCL: {type: 'net', value: 'SCL'},
    SDA: {type: 'net', value: 'SDA'},
  },
  body: p => {
    const back = p.side === 'B'
    const x = v => ((back ? -1 : 1) * v).toFixed(4)
    const L = l => back ? l.replace(/^([FB])\./, (_, s) => (s === 'F' ? 'B' : 'F') + '.') : l
    const mirror = back ? ' (justify mirror)' : ''
    const line = (x1, y1, x2, y2, layer, w) =>
      `(fp_line (start ${x(x1)} ${y1}) (end ${x(x2)} ${y2}) (stroke (width ${w}) (type solid)) (layer "${L(layer)}"))`
    const label = (t, lx) =>
      `(fp_text user "${t}" (at ${x(lx)} 2.159 ${p.r}) (layer "${L('F.SilkS')}") (effects (font (size 1 0.7) (thickness 0.15))${mirror}))`
    const hole = (hx, hy) =>
      `(pad "" np_thru_hole oval (at ${x(hx)} ${hy} ${p.r}) (size 3.8 2.9) (drill oval 3.8 2.9) (layers "*.Cu" "*.Mask"))`
    const pin = (n, shape, px, net) =>
      `(pad "${n}" thru_hole ${shape} (at ${x(px)} 0 ${p.r + 90}) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") ${net.str})`

    return `
  (footprint "oled_i2c"
    (layer "${L('F.Cu')}")
    ${p.at}
    (attr through_hole exclude_from_pos_files exclude_from_bom)

    (property "Reference" "${p.ref}"
      (at ${x(-0.2286)} 10.8712 ${p.r})
      (layer "${L('F.SilkS')}")
      (effects (font (size 1 1) (thickness 0.15))${mirror})
    )

    ${line(-13.716, -1.397, 13.716, -1.397, 'F.Fab', 0.12)}
    ${line(13.716, 25.781, -13.716, 25.781, 'F.Fab', 0.12)}
    ${line(-13.716, 25.781, -13.589, -1.397, 'F.Fab', 0.12)}
    ${line(-13.716, 3.81, 13.716, 3.81, 'F.Fab', 0.12)}
    ${line(-13.716, 20.701, 13.716, 20.701, 'F.Fab', 0.12)}
    ${line(13.716, 25.781, 13.716, -1.397, 'F.Fab', 0.12)}
    ${line(-2.54, -1.33, 5.14, -1.33, 'F.SilkS', 0.12)}
    ${line(-2.54, 1.33, -2.54, -1.33, 'F.SilkS', 0.12)}
    ${line(-2.54, 1.33, 5.14, 1.33, 'F.SilkS', 0.12)}
    ${line(-5.14, 1.33, -5.14, 0, 'F.SilkS', 0.12)}
    ${line(-3.81, 1.33, -5.14, 1.33, 'F.SilkS', 0.12)}
    ${line(5.14, 1.33, 5.14, -1.33, 'F.SilkS', 0.12)}
    ${label('SDA', 3.937)}
    ${label('SCL', 1.27)}
    ${label('VDD', -1.27)}
    ${label('GND', -3.81)}

    ${line(5.59, 1.927, 5.59, -1.8, 'F.CrtYd', 0.05)}
    ${line(-5.61, 1.927, 5.59, 1.927, 'F.CrtYd', 0.05)}
    ${line(-5.61, -1.8, -5.61, 1.927, 'F.CrtYd', 0.05)}
    ${line(5.59, -1.8, -5.61, -1.8, 'F.CrtYd', 0.05)}

    ${line(5.08, -1.27, 5.08, 1.27, 'F.Fab', 0.1)}
    ${line(5.08, 1.27, -4.445, 1.27, 'F.Fab', 0.1)}
    ${line(-5.08, 0.635, -5.08, -1.27, 'F.Fab', 0.1)}
    ${line(-5.08, -1.27, 5.08, -1.27, 'F.Fab', 0.1)}
    ${line(-4.445, 1.27, -5.08, 0.635, 'F.Fab', 0.1)}

    ${p.holes ? [hole(-11.176, 0.635), hole(11.176, 0.635), hole(11.176, 23.749), hole(-11.176, 23.749)].join('\n    ') : ''}

    ${pin(1, 'rect', -3.81, p.GND)}
    ${pin(2, 'oval', -1.27, p.VDD)}
    ${pin(3, 'oval', 1.27, p.SCL)}
    ${pin(4, 'oval', 3.81, p.SDA)}
    ${p.model && !back ? `(model "${p.model}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))` : ''}
  )
  `
  },
}
