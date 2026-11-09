# Print settings for the keycaps (Bambu A1, 0.2 nozzle, Polymaker matte PLA = PolyTerra), built from
# the Bambu Studio system presets installed on this PC plus our changes:
#   - project_settings(n_filaments): the full flat config Bambu Studio stores in a project 3MF
#     (Metadata/project_settings.config), used by bambu_project.py;
#   - write_presets(dir): importable user presets (File > Import > Import Configs in Bambu Studio):
#     "Keycaps 0.06 @BBL A1 0.2 nozzle" (process) and "PolyTerra PLA keycaps @BBL A1 0.2 nozzle"
#     (filament), each inheriting the system preset and holding only our changes.
# Per-object settings for the caps (supports, brim, seam, walls) stay in bambu_project.py.
# Usage: python keycaps/build/bambu_settings.py   -> keycaps/results/profiles/*.json
import os, sys, json, glob, re

STUDIO = os.path.join(os.environ.get('APPDATA', ''), 'BambuStudio')
SYSTEM = os.path.join(STUDIO, 'system', 'BBL')
PRINTER = 'Bambu Lab A1 0.2 nozzle'
PROCESS = '0.06mm High Quality @BBL A1 0.2 nozzle'
FILAMENT = 'PolyTerra PLA @BBL A1 0.2 nozzle'
PROCESS_NAME = 'Keycaps 0.06 @BBL A1 0.2 nozzle'
FILAMENT_NAME = 'PolyTerra PLA keycaps @BBL A1 0.2 nozzle'
COLOURS = ['#E8E6E1', '#1C1C1E']            # filament 1 (caps, inserts) / 2 (legends)

PROCESS_CHANGES = {
    'layer_height': '0.06', 'initial_layer_print_height': '0.1',     # legend = first 2 layers (0.16)
    'line_width': '0.22', 'outer_wall_line_width': '0.2', 'inner_wall_line_width': '0.22',
    'wall_generator': 'arachne', 'precise_outer_wall': '1',
    'outer_wall_speed': '40', 'outer_wall_acceleration': '1500',
    'seam_position': 'back', 'seam_slope_type': 'none',
    'reduce_crossing_wall': '1', 'ironing_type': 'no ironing', 'fuzzy_skin': 'none',
    'elefant_foot_compensation': '0.1',
    'enable_support': '0',                 # on per object (the caps), not for the inserts
    'support_type': 'tree(auto)', 'support_threshold_angle': '40', 'support_on_build_plate_only': '0',
    'support_top_z_distance': '0.12', 'support_interface_top_layers': '2', 'bridge_no_support': '1',
    'brim_type': 'no_brim',                # the caps get a 4 mm brim per object
}
FILAMENT_CHANGES = {'fan_min_speed': '80', 'fan_max_speed': '100', 'slow_down_layer_time': '8',
                    'slow_down_for_layer_cooling': '1'}
META = {'type', 'name', 'inherits', 'from', 'setting_id', 'instantiation', 'description', 'include'}
# preset-file keys Bambu Studio does not write into a project (seen in its own re-save of ours): left out
NOT_IN_PROJECT = {'adaptive_layer_height', 'extruder_clearance_radius', 'extruder_height_gap', 'filament_contact_safe',
                  'filament_emission_safe', 'filament_id', 'filament_ingredients_safe', 'filament_long_retractions_when_ec',
                  'filament_retraction_distances_when_ec', 'layer_time_smoothing', 'layer_time_smoothing_threshold',
                  'only_one_wall_top', 'wall_infill_order'}
# preset-level fields that a Bambu Studio project never has (a project it saved: none of these)
PRESET_ONLY = {'compatible_printers', 'compatible_printers_condition', 'compatible_prints',
               'compatible_prints_condition', 'inherits_group'}
# real options left at their built-in defaults in the BBL presets (names checked in BambuStudio.dll)
DEFAULTED = {'precise_outer_wall', 'fuzzy_skin', 'brim_type'}

_index = None


def preset(name):
    global _index
    if _index is None:
        _index = {}
        for f in glob.glob(os.path.join(SYSTEM, '**', '*.json'), recursive=True):
            try:
                d = json.load(open(f, encoding='utf-8'))
            except Exception:
                continue
            if isinstance(d, dict) and 'name' in d:
                _index[d['name']] = d
    d = _index[name]
    out = dict(preset(d['inherits']) if d.get('inherits') else {})
    for inc in d.get('include', []):              # Bambu's templates (start / end G-code etc.), then own keys
        out.update(preset(inc))
    out.update({k: v for k, v in d.items() if k not in META})
    return out


def apply(cfg, changes):
    """Set each change in the shape the preset uses (list values stay lists); unknown keys fail."""
    missing = [k for k in changes if k not in cfg and k not in DEFAULTED]
    if missing:
        raise KeyError('not in the preset: %s' % ', '.join(missing))
    for k, v in changes.items():
        cfg[k] = [v] * len(cfg[k]) if isinstance(cfg.get(k), list) else v
    return cfg


def studio_version():
    """Bambu Studio's version (BambuStudio.conf), written into the 3MF headers."""
    try:
        m = re.search(r'"version"\s*:\s*"([\d.]+)"', open(os.path.join(STUDIO, 'BambuStudio.conf'), encoding='utf-8').read())
        return m.group(1) if m else '02.08.02.61'
    except OSError:
        return '02.08.02.61'


def preset_version():
    """The installed BBL system preset version (for the user presets)."""
    try:
        return json.load(open(os.path.join(STUDIO, 'system', 'BBL.json'), encoding='utf-8'))['version']
    except (OSError, KeyError, ValueError):
        return '02.08.00.06'


def available():
    return os.path.isdir(SYSTEM)


TOWER = (195, 60)                           # prime tower corner on every plate: lower right, clear of the
                                            # insert grid and the caps (the default ran off the A1 bed)


def project_settings(n_filaments=2, n_plates=1):
    printer, process, fil = preset(PRINTER), apply(preset(PROCESS), PROCESS_CHANGES), apply(preset(FILAMENT), FILAMENT_CHANGES)
    cfg = {}
    cfg.update(printer); cfg.update(process)
    for k, v in fil.items():
        cfg[k] = (v * n_filaments) if isinstance(v, list) and len(v) == 1 else v
    fid = fil.get('filament_id', 'GFL99')
    for k in NOT_IN_PROJECT | PRESET_ONLY: cfg.pop(k, None)
    cfg['filament_colour'] = COLOURS[:n_filaments]
    cfg['wipe_tower_x'] = [str(TOWER[0])] * n_plates      # (one entry per plate)
    cfg['wipe_tower_y'] = [str(TOWER[1])] * n_plates
    # the per-filament fields Bambu Studio 2.x writes (as in a project it saved itself): its window
    # refuses a project whose filament lists don't match the filament count ("invalid config");
    # the CLI doesn't check, and its own re-save leaves them short
    n = n_filaments
    cfg.update({'filament_ids': [fid] * n, 'filament_self_index': [str(i + 1) for i in range(n)],
                'filament_map': ['1'] * n, 'filament_map_mode': 'Auto For Flush',
                'filament_nozzle_map': ['0'] * n, 'filament_volume_map': ['0'] * n,
                'extruder_ams_count': ['1#0|4#0', '1#0|4#0'], 'filament_multi_colour': COLOURS[:n],
                'filament_colour_type': ['0'] * n, 'filament_is_mixed': ['0'] * n,
                'default_filament_colour': [''] * n, 'flush_volumes_vector': ['140'] * (2 * n)})
    cfg.update({'name': 'project_settings', 'from': 'project', 'version': studio_version(),
                'printer_settings_id': PRINTER, 'print_settings_id': PROCESS,
                'filament_settings_id': [FILAMENT] * n_filaments,
                'different_settings_to_system': [';'.join(sorted(PROCESS_CHANGES))]
                + [';'.join(sorted(FILAMENT_CHANGES))] * n_filaments + ['']})
    if n_filaments > 1:                       # flushing between the 2 filaments (AMS lite)
        cfg['flush_volumes_matrix'] = ['0' if i == j else '280' for i in range(n_filaments) for j in range(n_filaments)]
    return cfg


def write_presets(out):
    os.makedirs(out, exist_ok=True)
    apply(preset(PROCESS), PROCESS_CHANGES); apply(preset(FILAMENT), FILAMENT_CHANGES)   # (checks the keys)
    proc, fil = preset(PROCESS), preset(FILAMENT)
    p = {'type': 'process', 'name': PROCESS_NAME, 'inherits': PROCESS, 'from': 'User', 'instantiation': 'true',
         'print_settings_id': PROCESS_NAME, 'version': preset_version()}
    p.update({k: ([v] * len(proc[k]) if isinstance(proc.get(k), list) else v) for k, v in PROCESS_CHANGES.items()})
    f = {'type': 'filament', 'name': FILAMENT_NAME, 'inherits': FILAMENT, 'from': 'User', 'instantiation': 'true',
         'filament_settings_id': [FILAMENT_NAME], 'version': preset_version()}
    f.update({k: ([v] * len(fil[k]) if isinstance(fil[k], list) else v) for k, v in FILAMENT_CHANGES.items()})
    paths = []
    for d in (p, f):
        path = os.path.join(out, d['name'] + '.json')
        json.dump(d, open(path, 'w', encoding='utf-8'), indent=4)
        paths.append(path)
    return paths


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'profiles')
    for p in write_presets(out): print(p)
    c = project_settings()
    print('project settings: %d keys, printer %s, process %s, filaments %s' % (
        len(c), c['printer_settings_id'], c['print_settings_id'], c['filament_settings_id']))
