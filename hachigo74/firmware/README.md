# hachigo74 firmware (QMK / Vial)

Built by GitHub Actions on every push to `hachigo74/firmware/` (workflow
`.github/workflows/firmware.yml`, Vial's QMK fork at a pinned commit). The files in
`hachigo74/` are generated: change `kle/hachigo74_keys.json` or the board, then run
`tools/lib/qmk_matrix.py` and `tools/lib/qmk_gen.py` (see `../CLAUDE.md`, Firmware).

## Getting and flashing the firmware

1. GitHub → **Actions** → the latest green **firmware** run → **Artifacts** →
   `hachigo74-firmware` (a zip with the `.uf2`).
2. Hold the Helios reset about 1 s and release (through the pin channel in the case floor, or on the bare
   board), or hold the **left arrow** key (left half, c2_r1) while plugging in. A drive
   called **RPI-RP2** appears.
3. Copy the `.uf2` onto it. The keyboard restarts with the new firmware.
4. Open the **Vial** app (get.vial.today, desktop or browser): it reads the layout from the
   keyboard. To unlock it for protected changes, hold **left Esc + right Backspace**.

## First test on the board

Test in this order; each step builds on the one before. Note what fails and where.

- [ ] **Flash:** the `.uf2` copies over and the keyboard shows up in Windows.
- [ ] **Keys:** type every key on layer 0 and on the Fn layer (a key tester, or Vial's
      *Matrix tester*). A whole dead row or column points to a matrix pin; a single dead key
      to its socket's solder joint or its diode.
- [ ] **Dual keys:**
  - outer thumb keys: hold = Shift, tap = one-shot Fn (the next key from the Fn layer);
  - right thumb (c7_r1): tap = Space, hold = Enter;
  - left c5_r1: hold = Ctrl, tap = Tab;
  - right c3_r1: hold = AltGr, tap = Alt;
  - the `(` `)` `@` keys give `{` `}` `*` with AltGr.
- [ ] **LEDs:** every key lit dim white; both indicator LEDs green while Fn is held (and
      while a one-shot Fn waits), off otherwise.
- [ ] **OLED:** text the right way up (if not: a one-line change, the module's rotation),
      showing the layer (Base / Fn) and the KPM of the last 10 s.
- [ ] **Trackpad:** pointer direction (if mirrored or rotated: a one-line change), tap to
      click, circular scroll along the edge.
- [ ] **Vial:** the layout appears on its own; remap a key and check it sticks after
      unplugging; the unlock combo; the tapping term under *QMK Settings*.
