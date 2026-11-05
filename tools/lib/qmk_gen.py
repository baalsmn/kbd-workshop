# QMK keyboard + Vial keymap from the routed board's matrix (tools/lib/qmk_matrix.py ->
# <keyboard>/firmware/matrix.json) and the KLE key map (<keyboard>/kle/<name>_keys.json).
# Usage: python tools/lib/qmk_gen.py hachigo74
#   -> hachigo74/firmware/hachigo74/{keyboard.json, config.h, rules.mk, hachigo74.h, hachigo74.c,
#      keymaps/vial/{keymap.c, rules.mk, config.h, vial.json}}; the workflow copies it into
#      vial-qmk's keyboards/ (Vial: the layout is stored on the keyboard, no file to load).
#
# KLE legend slots (as the key maps are drawn): 4 front = QMK keycode, 6 centre-left = the
# base character, 1 / 3 bottom = Windows AltGr characters, 2 top-right = an Fn-layer key of
# the user's, 7 centre-right = the Fn layer.
# Layer 1 (Fn) per key: the centre-right legend, else the top-right one, else the key's
# Windows Hungarian AltGr character (QMK keymap_hungarian.h), except the ones the user moved
# ($ on S, EUR on E: not on E-acute / U).
import sys, os, json, math
NAME = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(ROOT, NAME)
M = json.load(open(os.path.join(KB, 'firmware', 'matrix.json'), encoding='utf-8'))
KLE = json.load(open(os.path.join(KB, 'kle', NAME + '_keys.json'), encoding='utf-8'))['keys']
OUT = os.path.join(KB, 'firmware', NAME)
os.makedirs(OUT, exist_ok=True)

# ---- pins (Helios GPIO, checked against the board's MCU1 nets) ----
ROW_PIN = {'R1': 'GP22', 'R2': 'GP26', 'R3': 'GP27', 'R4': 'GP28', 'R5': 'GP29',
           'R6': 'GP6', 'R7': 'GP5', 'R8': 'GP4', 'R9': 'GP1', 'R10': 'GP0'}
COL_PIN = {'C1': 'GP8', 'C2': 'GP9', 'C3': 'GP12', 'C4': 'GP13', 'C5': 'GP14', 'C6': 'GP15',
           'C7': 'GP16', 'C8': 'GP21', 'C9': 'GP23'}
rows = sorted({k['row'] for k in M['keys']}, key=lambda s: int(s[1:]))
cols = sorted({k['col'] for k in M['keys']}, key=lambda s: int(s[1:]))
RI = {r: i for i, r in enumerate(rows)}; CI = {c: i for i, c in enumerate(cols)}

# ---- key order of the LAYOUT macro: left half rows 5..1, c2..c9; right half rows 5..1, c9..c2 ----
def rc(name):
    c, r = name.split('_')[-2:]; return int(c[1:]), int(r[1:])
left = [k for k in M['keys'] if not k['name'].startswith('mirror_')]
right = [k for k in M['keys'] if k['name'].startswith('mirror_')]
left.sort(key=lambda k: (-rc(k['name'])[1], rc(k['name'])[0]))
right.sort(key=lambda k: (-rc(k['name'])[1], -rc(k['name'])[0]))
keys = left + right

def legends(name):
    L = KLE[name]['label'].split('\n') + [''] * 12
    return L

# ---- layer 0 ----
SPECIAL0 = {   # key name (without hand-zone prefix) -> keycode, by the KLE's hold / tap legends
    'hand-zone_c5_r1': 'LCTL_T(KC_TAB)',          # Hold: LCtrl, Tap: Tab
    'hand-zone_c9_r1': 'SFT_FN',                  # Hold: Shift, Tap: one-shot Fn layer
    'mirror_hand-zone_c9_r1': 'SFT_FN',
    'mirror_hand-zone_c3_r1': 'RALT_T(KC_LALT)',  # Hold: AltGr, Tap: Alt
    'mirror_hand-zone_c7_r1': 'SPC_ENT',          # Tap: Space, Hold: Enter
    'mirror_hand-zone_c2_r1': 'MO(1)',            # Fn
    'hand-zone_c9_r2': 'HU_PAREN_L',              # ( ; AltGr: {
    'mirror_hand-zone_c9_r2': 'HU_PAREN_R',       # ) ; AltGr: }
    'mirror_hand-zone_c3_r2': 'HU_AT_ASTR',       # @ ; AltGr: *
}
def base_code(k):
    if k['name'] in SPECIAL0: return SPECIAL0[k['name']]
    q = legends(k['name'])[4].strip()
    return 'KC_' + q

# ---- layer 1 ----
ALTGR = {   # Windows Hungarian AltGr layer, by base keycode (QMK keymap_hungarian.h)
    'KC_1': 'HU_TILD', 'KC_3': 'HU_CIRC', 'KC_7': 'HU_GRV', 'KC_0': 'HU_DACU', 'KC_MINS': 'HU_DIAE',
    'KC_EQL': 'HU_CEDL', 'KC_Q': 'HU_BSLS', 'KC_W': 'HU_PIPE', 'KC_E': 'HU_CADI', 'KC_U': 'HU_EURO',
    'KC_LBRC': 'HU_DIV', 'KC_RBRC': 'HU_MUL', 'KC_A': 'HU_LADI', 'KC_S': 'HU_LDST', 'KC_D': 'HU_CDST',
    'KC_F': 'HU_LBRC', 'KC_G': 'HU_RBRC', 'KC_K': 'HU_LLST', 'KC_L': 'HU_CLST', 'KC_SCLN': 'HU_DLR',
    'KC_QUOT': 'HU_SS', 'KC_NUHS': 'HU_CURR', 'KC_NUBS': 'HU_LABK', 'KC_Z': 'HU_RABK', 'KC_X': 'HU_HASH',
    'KC_C': 'HU_AMPR', 'KC_V': 'HU_AT', 'KC_B': 'HU_LCBR', 'KC_N': 'HU_RCBR', 'KC_COMM': 'HU_SCLN',
    'KC_SLSH': 'HU_ASTR',
}
MOVED = {'KC_SCLN', 'KC_U'}         # $ and EUR: on S / E as drawn in the KLE, not on E-acute / U
LEGEND = {   # legend text -> keycode on the Fn layer
    **{'F%d' % i: 'KC_F%d' % i for i in range(1, 13)},
    '[': 'HU_LBRC', ']': 'HU_RBRC', '<': 'HU_LABK', '>': 'HU_RABK', '~': 'HU_TILD',
    '$': 'HU_DLR', '€': 'HU_EURO', 'End': 'KC_END', 'PrtSc': 'KC_PSCR', 'Undo': 'C(HU_Z)',
}
def fn_code(k):
    L = legends(k['name'])
    for slot in (7, 2):
        t = L[slot].strip()
        if t:
            if t not in LEGEND: sys.exit('%s: no keycode for Fn legend %r' % (k['name'], t))
            return LEGEND[t]
    b = base_code(k)
    if b in ALTGR and b not in MOVED: return ALTGR[b]
    return '_______'

layer0 = [base_code(k) for k in keys]
layer1 = [fn_code(k) for k in keys]
args = ['k%d%d' % (RI[k['row']], CI[k['col']]) for k in keys]

# ---- keyboard.json ----
U = 19.05
minx = min(k['px'] for k in keys); maxy = max(k['py'] for k in keys)
layout = []
for k, a in zip(keys, args):
    w = k['u']
    cx, cy = (k['px'] - minx) / U + 0.5, (maxy - k['py']) / U + 0.5     # key centre, in key units
    side = 'R_' if k['name'].startswith('mirror_') else 'L_'
    item = {'label': side + k['name'].split('hand-zone_')[1],
            'matrix': [RI[k['row']], CI[k['col']]], 'x': round(cx - w / 2, 3), 'y': round(cy - 0.5, 3)}
    if w != 1: item['w'] = w
    if k['pr']: item.update({'r': round(-k['pr'], 3), 'rx': round(cx, 3), 'ry': round(cy, 3)})
    layout.append(item)
# RGB matrix: every LED in chain order, position scaled to 0..224 x 0..64
lx = [l['x'] for l in M['leds']]; ly = [l['y'] for l in M['leds']]
sx = 224 / (max(lx) - min(lx)); sy = 64 / (max(ly) - min(ly))
key_of_led = {k['led']: k for k in M['keys']}
rgb = []
for l in sorted(M['leds'], key=lambda l: l['index']):
    e = {'x': round((l['x'] - min(lx)) * sx), 'y': round((l['y'] - min(ly)) * sy)}
    k = key_of_led.get(l['index'])
    if k: e = {'matrix': [RI[k['row']], CI[k['col']]], **e, 'flags': 4}
    else: e['flags'] = 8
    rgb.append(e)
kbjson = {
    'keyboard_name': NAME, 'manufacturer': 'keyboard-workshop', 'maintainer': 'baalsmn',
    'usb': {'vid': '0xFEED', 'pid': '0x0074' if NAME == 'hachigo74' else '0x0082', 'device_version': '1.0.0'},
    'processor': 'RP2040', 'bootloader': 'rp2040', 'board': 'QMK_PM2040',
    'diode_direction': 'COL2ROW',
    'matrix_pins': {'cols': [COL_PIN[c] for c in cols], 'rows': [ROW_PIN[r] for r in rows]},
    'features': {'bootmagic': True, 'extrakey': True, 'mousekey': True, 'nkro': True,
                 'rgb_matrix': True, 'oled': True, 'pointing_device': True},
    'ws2812': {'driver': 'vendor', 'pin': 'GP25'},
    'rgb_matrix': {'driver': 'ws2812', 'max_brightness': 40, 'sleep': True,
                   'default': {'animation': 'solid_color', 'sat': 0, 'val': 40},
                   'animations': {'solid_color': True, 'breathing': True, 'cycle_all': True,
                                  'cycle_left_right': True, 'rainbow_moving_chevron': True,
                                  'solid_reactive_simple': True},
                   'layout': rgb},
    'layouts': {'LAYOUT': {'layout': layout}},
}
open(os.path.join(OUT, 'keyboard.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(kbjson, indent=4, ensure_ascii=False) + '\n')

# bootmagic (bootloader when held while plugging in) is QMK's default matrix [0, 0] = R1 / C2:
# the left half's c2_r1 (left arrow), so keyboard.json doesn't repeat it (qmk lint)
assert RI['R1'] == 0 and CI['C2'] == 0

# ---- readme.md (required by qmk lint) ----
open(os.path.join(OUT, 'readme.md'), 'w', encoding='utf-8', newline='\n').write('''# %(n)s

Split ergonomic keyboard on one PCB (%(k)d keys, Gateron KS-33 hot-swap, per-key RGB, Cirque
trackpad, OLED) with a 0xCB Helios (RP2040). Design files: https://github.com/baalsmn/keyboard-workshop

* Keyboard maintainer: baalsmn
* Hardware supported: %(n)s PCB, 0xCB Helios
* Hardware availability: private project

Make example for this keyboard (after setting up your build environment):

    qmk compile -kb %(n)s -km vial      (in vial-qmk)

Bootloader: hold the Helios reset ~1 s and release, or hold the key at matrix [0, 0] (the left half's
left arrow) while plugging in. Then copy the .uf2 onto the RPI-RP2 drive.

Generated by tools/lib/qmk_gen.py in the design repository; edit the generator, not this file.
''' % {'n': NAME, 'k': len(keys)})

# ---- config.h / rules.mk ----
open(os.path.join(OUT, 'config.h'), 'w', encoding='utf-8', newline='\n').write('''// %s, generated by tools/lib/qmk_gen.py
#pragma once

// I2C1 on the Helios: SDA GP2, SCL GP3, shared by the OLED (0x3C) and the Cirque (0x2A)
#define I2C_DRIVER I2CD1
#define I2C1_SDA_PIN GP2
#define I2C1_SCL_PIN GP3

// 0.96" SSD1306 128x64 (QMK's default is 128x32)
#define OLED_DISPLAY_128X64

// Cirque TM040040 (I2C, flat overlay; its DR line on GP7 is not used, the driver polls)
#define CIRQUE_PINNACLE_DIAMETER_MM 40
#define CIRQUE_PINNACLE_TAP_ENABLE
#define POINTING_DEVICE_GESTURES_SCROLL_ENABLE

// 76 LEDs at 37 mA full white = 2.8 A: brightness is capped in keyboard.json (40/255)
// Indicator LEDs (chain index): off on layer 0, green on layer 1
#define INDICATOR_LEDS {%s}
// (three separate values: the SET_COLOR macro counts its arguments before expanding them)
#define INDICATOR_FN_R 0
#define INDICATOR_FN_G 96
#define INDICATOR_FN_B 0
''' % (NAME, ', '.join(str(i) for i in M['indicators'])))
open(os.path.join(OUT, 'rules.mk'), 'w', encoding='utf-8', newline='\n').write(
    '# %s, generated by tools/lib/qmk_gen.py\nPOINTING_DEVICE_DRIVER = cirque_pinnacle_i2c\nOLED_DRIVER = ssd1306\n' % NAME)

# ---- <name>.h: keyboard-level keycodes (QK_KB_*, so Vial can assign them too) ----
open(os.path.join(OUT, NAME + '.h'), 'w', encoding='utf-8', newline='\n').write('''// %(n)s, generated by tools/lib/qmk_gen.py
#pragma once
#include "quantum.h"

enum %(n)s_keycodes {
    HU_PAREN_L = QK_KB_0, // ( ; with AltGr: {
    HU_PAREN_R,           // ) ; with AltGr: }
    HU_AT_ASTR,           // @ ; with AltGr: *
};

// hold: Shift, tap: one-shot Fn layer (a mod-tap whose tap is replaced in process_record_kb)
#define SFT_FN LSFT_T(KC_F18)
// tap: Space, hold: Enter (a layer-tap on layer 0 whose hold is replaced)
#define SPC_ENT LT(0, KC_SPC)
''' % {'n': NAME})

# ---- <name>.c: custom keys, KPM, OLED, indicators ----
C_SRC = r'''// @N@, generated by tools/lib/qmk_gen.py
#include QMK_KEYBOARD_H
#include "keymap_hungarian.h"

// ---- keys per minute: key presses in ten 1 s slots, the sum of the last 10 s x 6 ----
#define KPM_SLOTS 10
static uint16_t kpm_slot[KPM_SLOTS];
static uint8_t  kpm_now;
static uint32_t kpm_slot_start;

static void kpm_advance(void) {
    while (timer_elapsed32(kpm_slot_start) >= 1000) {
        kpm_slot_start += 1000;
        kpm_now = (kpm_now + 1) % KPM_SLOTS;
        kpm_slot[kpm_now] = 0;
    }
}

uint16_t kpm_get(void) {
    kpm_advance();
    uint16_t sum = 0;
    for (uint8_t i = 0; i < KPM_SLOTS; i++) sum += kpm_slot[i];
    return sum * (60 / KPM_SLOTS);
}

void keyboard_post_init_kb(void) {
    kpm_slot_start = timer_read32();
    keyboard_post_init_user();
}

static bool fn_active(void) {
    return layer_state_is(1) || (get_oneshot_layer() == 1 && get_oneshot_layer_state());
}

// ---- keys whose AltGr character is not the one Windows puts on that key position ----
static uint16_t held_code[3];

static bool altgr_key(uint8_t i, uint16_t plain, uint16_t with_altgr, keyrecord_t *record) {
    if (record->event.pressed) {
        held_code[i] = (get_mods() & MOD_BIT(KC_RALT)) ? with_altgr : plain;
        register_code16(held_code[i]);
    } else {
        unregister_code16(held_code[i]);
    }
    return false;
}

bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    if (record->event.pressed) {
        kpm_advance();
        if (kpm_slot[kpm_now] < UINT16_MAX) kpm_slot[kpm_now]++;
    }
    if (!process_record_user(keycode, record)) return false;
    switch (keycode) {
        case HU_PAREN_L: return altgr_key(0, HU_LPRN, HU_B, record);    // AltGr + B = {
        case HU_PAREN_R: return altgr_key(1, HU_RPRN, HU_N, record);    // AltGr + N = }
        case HU_AT_ASTR: return altgr_key(2, HU_AT, HU_MINS, record);   // AltGr + - = *
        case SFT_FN:
            if (record->tap.count) {                                    // tapped: one-shot Fn
                if (record->event.pressed) {
                    set_oneshot_layer(1, ONESHOT_START);
                } else {
                    clear_oneshot_layer_state(ONESHOT_PRESSED);
                }
                return false;
            }
            return true;                                                // held: Shift
        case SPC_ENT:
            if (!record->tap.count) {                                   // held: Enter
                if (record->event.pressed) {
                    register_code(KC_ENT);
                } else {
                    unregister_code(KC_ENT);
                }
                return false;
            }
            return true;                                                // tapped: Space
    }
    return true;
}

#ifdef OLED_ENABLE
// the module is mounted turned round (header towards the user)
oled_rotation_t oled_init_kb(oled_rotation_t rotation) {
    return OLED_ROTATION_180;
}

// ---- status screen in a 9 x 12 font (tools/lib/oled_font.py), drawn pixel by pixel ----
#define FONT_W 9
#define FONT_H 14
#define ROW_Y(n) ((n) * 17)
static const char font_chars[] = "@FONT_CHARS@";
static const uint8_t font_rows[][FONT_H] = {
@FONT_ROWS@
};

static void draw_char(uint8_t x, uint8_t y, char c) {
    uint8_t g = 0;                                                      // unknown character: blank
    for (uint8_t i = 0; font_chars[i]; i++) {
        if (font_chars[i] == c) {
            g = i;
            break;
        }
    }
    for (uint8_t r = 0; r < FONT_H; r++) {
        for (uint8_t col = 0; col < FONT_W; col++) {
            oled_write_pixel(x + col, y + r, col < 8 && (font_rows[g][r] & (0x80 >> col)));
        }
    }
}

// text from x, padded with blanks to `width` characters so a shorter value clears the longer one
static void draw_text(uint8_t x, uint8_t y, const char *s, uint8_t width) {
    for (uint8_t i = 0; i < width; i++) {
        draw_char(x + i * FONT_W, y, *s ? *s : ' ');
        if (*s) s++;
    }
}

// right-aligned text ending at the screen's right edge, cleared to `width` characters
static void draw_right(uint8_t y, const char *s, uint8_t width) {
    uint8_t n = 0;
    while (s[n]) n++;
    uint8_t x = 128 - width * FONT_W;
    draw_text(x, y, "", width - n);
    draw_text(x + (width - n) * FONT_W, y, s, n);
}

// a number as text, optionally with a percent sign; returns its first character in buf (8 bytes)
static const char *num_text(char *buf, uint16_t v, bool percent) {
    uint8_t i = 7;
    buf[i] = 0;
    if (percent) buf[--i] = '%';
    do {
        buf[--i] = '0' + v % 10;
        v /= 10;
    } while (v);
    return buf + i;
}

static const char *layer_name(void) {
    switch (get_highest_layer(layer_state | default_layer_state)) {
        case 0: return "BASE";
        case 1: return "HIGH";
        case 2: return "LOW";
        default: return "L3";
    }
}

#ifdef RGB_MATRIX_ENABLE
static const char *rgb_name(void) {
    if (!rgb_matrix_is_enabled()) return "OFF";
    switch (rgb_matrix_get_mode()) {
        case RGB_MATRIX_SOLID_COLOR: return "SOL";
        case RGB_MATRIX_BREATHING: return "BRE";
        case RGB_MATRIX_CYCLE_ALL: return "CYC";
        case RGB_MATRIX_CYCLE_LEFT_RIGHT: return "CLR";
        case RGB_MATRIX_RAINBOW_MOVING_CHEVRON: return "CHV";
        case RGB_MATRIX_SOLID_REACTIVE_SIMPLE: return "REA";
        default: return "---";
    }
}

// the effects that have a speed: not solid colour, off or an unknown one
static bool rgb_uses_speed(void) {
    if (!rgb_matrix_is_enabled()) return false;
    switch (rgb_matrix_get_mode()) {
        case RGB_MATRIX_BREATHING:
        case RGB_MATRIX_CYCLE_ALL:
        case RGB_MATRIX_CYCLE_LEFT_RIGHT:
        case RGB_MATRIX_RAINBOW_MOVING_CHEVRON:
        case RGB_MATRIX_SOLID_REACTIVE_SIMPLE:
            return true;
        default:
            return false;
    }
}
#endif

bool oled_task_kb(void) {
    if (!oled_task_user()) return false;
    static uint32_t last_draw;
    if (timer_elapsed32(last_draw) < 50) return false;
    last_draw = timer_read32();
    char buf[8];

    // left column: layer, FN, CAPS
    draw_text(0, ROW_Y(0), layer_name(), 4);
    draw_text(0, ROW_Y(1), fn_active() ? "FN" : "", 4);
    draw_text(0, ROW_Y(2), host_keyboard_led_state().caps_lock ? "CAPS" : "", 4);

    // right column: RGB effect, brightness (% of the firmware's cap), effect speed, KPM
#ifdef RGB_MATRIX_ENABLE
    draw_right(ROW_Y(0), rgb_name(), 4);
    draw_right(ROW_Y(1), num_text(buf, (rgb_matrix_get_val() * 100U + RGB_MATRIX_MAXIMUM_BRIGHTNESS / 2) / RGB_MATRIX_MAXIMUM_BRIGHTNESS, true), 4);
    draw_right(ROW_Y(2), rgb_uses_speed() ? num_text(buf, (rgb_matrix_get_speed() * 100U + 127) / 255, true) : "", 4);
#endif
    draw_right(ROW_Y(3), num_text(buf, kpm_get(), false), 5);
    return false;
}
#endif

#ifdef RGB_MATRIX_ENABLE
static const uint8_t indicator_leds[] = INDICATOR_LEDS;

bool rgb_matrix_indicators_advanced_kb(uint8_t led_min, uint8_t led_max) {
    if (!rgb_matrix_indicators_advanced_user(led_min, led_max)) return false;
    bool fn = fn_active();
    for (uint8_t i = 0; i < sizeof(indicator_leds); i++) {
        if (fn) {
            RGB_MATRIX_INDICATOR_SET_COLOR(indicator_leds[i], INDICATOR_FN_R, INDICATOR_FN_G, INDICATOR_FN_B);
        } else {
            RGB_MATRIX_INDICATOR_SET_COLOR(indicator_leds[i], 0, 0, 0);
        }
    }
    return true;
}
#endif
'''
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oled_font import c_table
FONT_CHARS, FONT_ROWS = c_table()
open(os.path.join(OUT, NAME + '.c'), 'w', encoding='utf-8', newline='\n').write(
    C_SRC.replace('@N@', NAME).replace('@FONT_CHARS@', FONT_CHARS).replace('@FONT_ROWS@', FONT_ROWS))

# ---- keymap "vial": keymap.c, rules.mk, config.h, vial.json (built with vial-qmk) ----
KM = os.path.join(OUT, 'keymaps', 'vial')
os.makedirs(KM, exist_ok=True)
def grid(codes):
    out, w = [], max(len(c) for c in codes) + 1
    for i, (k, c) in enumerate(zip(keys, codes)):
        out.append('        %-*s // %s' % (w + 1, c + ',' if i < len(codes) - 1 else c, k['name'].replace('hand-zone_', '')))
    return '\n'.join(out)
open(os.path.join(KM, 'keymap.c'), 'w', encoding='utf-8', newline='\n').write('''// %(n)s keymap, generated by tools/lib/qmk_gen.py from kle/%(n)s_keys.json.
// Host: Windows with the Hungarian layout (HU_* keycodes). Layer 0 = base, layer 1 = Fn:
// F1-F12 and the AltGr characters, each on its Windows AltGr key ($ on S, EUR on E).
// The custom keys (HU_PAREN_L/R, HU_AT_ASTR, SFT_FN, SPC_ENT) are in %(n)s.c / .h.
// Vial is on: this is the keymap loaded on first start (or after an EEPROM reset).
#include QMK_KEYBOARD_H
#include "keymap_hungarian.h"

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
%(l0)s
    ),
    [1] = LAYOUT(
%(l1)s
    ),
};
''' % {'n': NAME, 'l0': grid(layer0), 'l1': grid(layer1)})
open(os.path.join(KM, 'rules.mk'), 'w', encoding='utf-8', newline='\n').write(
    '# %s Vial keymap, generated by tools/lib/qmk_gen.py\nVIA_ENABLE = yes\nVIAL_ENABLE = yes\nVIALRGB_ENABLE = yes\n' % NAME)
# keyboard UID: fixed per keyboard name (Vial tells keyboards apart by it)
import hashlib
uid = hashlib.sha256(('keyboard-workshop/' + NAME).encode()).digest()[:8]
# unlock combo (hold both in the Vial app to unlock): left Esc + right Backspace
UNLOCK = [k for k in M['keys'] if k['name'] in ('hand-zone_c3_r5', 'mirror_hand-zone_c3_r5')]
assert len(UNLOCK) == 2
open(os.path.join(KM, 'config.h'), 'w', encoding='utf-8', newline='\n').write('''// %s Vial keymap, generated by tools/lib/qmk_gen.py
#pragma once

#define VIAL_KEYBOARD_UID {%s}
// unlock combo: left Esc + right Backspace
#define VIAL_UNLOCK_COMBO_ROWS {%s}
#define VIAL_UNLOCK_COMBO_COLS {%s}
// layers shown in Vial (0 base, 1 Fn, 2-3 spare)
#define DYNAMIC_KEYMAP_LAYER_COUNT 4
''' % (NAME, ', '.join('0x%02X' % b for b in uid), ', '.join(str(RI[k['row']]) for k in UNLOCK), ', '.join(str(CI[k['col']]) for k in UNLOCK)))

# vial.json: the layout as KLE rows, one key each (r / rx / ry reset the position to the
# rotation centre, x / y offset from it); Vial reads it from the keyboard, no file to load
kle = []
for item in layout:
    p = {'r': item.get('r', 0), 'rx': item.get('rx', 0), 'ry': item.get('ry', 0)}
    p['x'] = round(item['x'] - p['rx'], 3); p['y'] = round(item['y'] - p['ry'], 3)
    if item.get('w', 1) != 1: p['w'] = item['w']
    kle.append([p, '%d,%d' % tuple(item['matrix'])])
vial = {
    'name': NAME, 'vendorId': kbjson['usb']['vid'], 'productId': kbjson['usb']['pid'],
    'lighting': 'vialrgb',
    'matrix': {'rows': len(rows), 'cols': len(cols)},
    'customKeycodes': [
        {'name': '( {', 'title': 'HU_PAREN_L: ( , with AltGr {', 'shortName': '( {'},
        {'name': ') }', 'title': 'HU_PAREN_R: ) , with AltGr }', 'shortName': ') }'},
        {'name': '@ *', 'title': 'HU_AT_ASTR: @ , with AltGr *', 'shortName': '@ *'},
    ],
    'layouts': {'keymap': kle},
}
open(os.path.join(KM, 'vial.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(vial, indent=1, ensure_ascii=False) + '\n')
print('%s: %d keys, %d x %d matrix, %d LEDs (indicators %s) -> %s' % (NAME, len(keys), len(rows), len(cols), len(rgb), M['indicators'], os.path.relpath(OUT, ROOT)))
print('layer 1: %d keys set; Vial keymap: %s' % (sum(1 for c in layer1 if c != '_______'), os.path.relpath(KM, ROOT)))
