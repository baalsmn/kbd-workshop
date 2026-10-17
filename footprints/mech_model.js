// Mechanical 3D model holder: a pad-less footprint that only places a 3D model
// (e.g. the trackpad, which is cabled rather than soldered). Excluded from the
// BOM and position files.
//
// model:          path to a STEP/WRL file
// model_offset:   [x, y, z] in mm (model frame: y up = north, z up from the PCB top)
// model_rotation: [x, y, z] in degrees
// label:          text on the Fab layer

module.exports = {
  params: {
    designator: 'MECH',
    label: '',
    model: '',
    model_offset: [0, 0, 0],
    model_rotation: [0, 0, 0],
  },
  body: p => `
  (footprint "mech_model"
    (layer "F.Cu")
    ${p.at}
    (attr exclude_from_pos_files exclude_from_bom)
    (property "Reference" "${p.ref}"
      (at 0 0 ${p.r})
      (layer "F.Fab")
      (effects (font (size 1 1) (thickness 0.15)))
    )
    (fp_text user "${p.label}" (at 0 1.5 ${p.r}) (layer "F.Fab")
      (effects (font (size 1 1) (thickness 0.15))))
    ${p.model ? `(model "${p.model}"
      (offset (xyz ${p.model_offset.join(' ')})) (scale (xyz 1 1 1)) (rotate (xyz ${p.model_rotation.join(' ')})))` : ''}
  )
  `,
}
